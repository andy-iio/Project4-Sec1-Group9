from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from tcp_client import TCPClient
import time
import base64
import os

app = Flask(__name__)
app.secret_key = 'preppers2025'  # Any string works for a project

# Create a global client instance
tcp_client = TCPClient(server_host='localhost', server_port=5001)

# Create uploads directory if it doesn't exist
os.makedirs('static/images/uploads', exist_ok=True)

def get_homepage_images():
    """Get images for home page from server"""
    success, response = tcp_client.send_request("GET_IMAGES", {})
    
    if success and response['body']['command'] == 'IMAGES':
        return response['body']['data'].get('images', [])
    else:
        # Log the error
        app.logger.error(f"Failed to get images: {response}")
        return []

def get_saved_images(user_id):
    """Get saved images for a user from server"""
    success, response = tcp_client.send_request("GET_SAVED_IMAGES", {"user_id": user_id})
    
    if success and response['body']['command'] == 'SAVED_IMAGES':
        return response['body']['data'].get('images', [])
    else:
        # Log the error
        app.logger.error(f"Failed to get saved images: {response}")
        return []

# Home page
@app.route('/home')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    images = get_homepage_images()
    return render_template('index.html', images=images, username=session.get('username'))

# Login page
@app.route('/')
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

# Process login
@app.route('/process_login', methods=['POST'])
def process_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Use TCP client to authenticate
    success, response = tcp_client.send_request("LOGIN", {
        "username": username,
        "password": password
    })
    
    if success and response['body']['command'] == 'LOGIN_SUCCESS':
        # Store user info in session
        session['user_id'] = response['body']['data']['user_id']
        session['username'] = response['body']['data']['username']
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error="Invalid username or password")

# Register page
@app.route('/register')
def register():
    return render_template('register.html')

# Process registration
@app.route('/process_register', methods=['POST'])
def process_register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    # Use TCP client to register
    success, response = tcp_client.send_request("REGISTER", {
        "username": username,
        "password": password,
        "email": email
    })
    
    if success and response['body']['command'] == 'REGISTER_SUCCESS':
        # Automatically log in the new user
        session['user_id'] = response['body']['data']['user_id']
        session['username'] = response['body']['data']['username']
        return redirect(url_for('index'))
    else:
        error_message = "Registration failed"
        if 'message' in response['body']['data']:
            error_message = response['body']['data']['message']
        return render_template('register.html', error=error_message)

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Saved page 
@app.route('/saved')
def saved():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    images = get_saved_images(session['user_id'])
    return render_template('saved-section.html', images=images, username=session.get('username'))

# Profile page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    return render_template('profile.html', username=session.get('username'))

# Image uploads
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
    # Gets info from form
    image = request.files['image']
    caption = request.form.get('caption', '')
    tags = request.form.get('tags', '')
    
    # Handles case where no file is selected
    if image.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    # Need to encode the image to base64 to be able to send it
    image_content = image.read()
    base64_image = base64.b64encode(image_content).decode('utf-8')

    data = {
        'filename': image.filename,
        'caption': caption,
        'tags': tags,
        'user_id': session['user_id'],
        'image': base64_image
    }

    success, response = tcp_client.send_request("UPLOAD_IMAGE", data)

    if success and response['body']['command'] == 'UPLOAD_SUCCESS':
        return jsonify({
            'status': 'success',
            'filename': image.filename,
            'caption': caption,
            'tags': tags,
            'image_id': response['body']['data']['image_id']
        })
    else:
        error_message = "Upload failed"
        if 'message' in response['body']['data']:
            error_message = response['body']['data']['message']
        return jsonify({'status': 'error', 'message': error_message})

# Save an image
@app.route('/api/save_image', methods=['POST'])
def save_image():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
    image_id = request.json.get('image_id')
    
    if not image_id:
        return jsonify({'status': 'error', 'message': 'No image ID provided'}), 400
    
    success, response = tcp_client.send_request("SAVE_IMAGE", {
        'user_id': session['user_id'],
        'image_id': image_id
    })
    
    if success and response['body']['command'] == 'SAVE_IMAGE_SUCCESS':
        return jsonify({'status': 'success'})
    else:
        error_message = "Failed to save image"
        if 'message' in response['body']['data']:
            error_message = response['body']['data']['message']
        return jsonify({'status': 'error', 'message': error_message})

# Unsave an image
@app.route('/api/unsave_image', methods=['POST'])
def unsave_image():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
    image_id = request.json.get('image_id')
    
    if not image_id:
        return jsonify({'status': 'error', 'message': 'No image ID provided'}), 400
    
    success, response = tcp_client.send_request("UNSAVE_IMAGE", {
        'user_id': session['user_id'],
        'image_id': image_id
    })
    
    if success and response['body']['command'] == 'UNSAVE_IMAGE_SUCCESS':
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to unsave image'})

# API endpoint to check TCP connection
@app.route('/api/check_connection')
def check_connection():
    if not tcp_client.connected:
        if not tcp_client.connect():
            return jsonify({"status": "disconnected", "message": "Failed to connect to server"})
    
    # Test the connection with a simple ping
    success, response = tcp_client.send_request("PING", {"timestamp": time.time()})
    
    if success:
        return jsonify({
            "status": "connected",
            "message": "Successfully connected to server",
            "response": response['body']['data'] if 'data' in response['body'] else None
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Error communicating with server: {response}"
        })

if __name__ == '__main__':
    # Connect to the server
    print("\n")
    print("#" * 70)
    print("CONNECTING TO TCP SERVER ON PORT 5001")
    print("#" * 70)
    
    tcp_client.connect()
    
    print("\n")
    print("#" * 70)
    print("STARTING CLIENT APP")
    print("CLIENT URL: http://127.0.0.1:5002")
    print("CLIENT URL: http://localhost:5002")
    print("#" * 70)
    print("\n")
    
    # Run Flask app
    app.run(debug=True, port=5002)