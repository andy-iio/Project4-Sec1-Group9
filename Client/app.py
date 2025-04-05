from flask import Flask, render_template, request, jsonify, redirect, url_for
from tcp_client import TCPClient
import time

app = Flask(__name__)

# Create a global client instance
tcp_client = TCPClient(server_host='localhost', server_port=5001)

#temporary for now, we will need to set up the getting of images through the server
def get_homepage_images():
    # Use TCP client to fetch images
    success, response = tcp_client.send_request("GET_IMAGES", {})
    
    if success:
        # In a real implementation, response would contain the images
        # For now, return the static list
        return [
            {"id": 1, "url": "./static/images/1.jpg", "caption": "caption for image 1", "category": "category 1"},
            {"id": 2, "url": "./static/images/2.jpg", "caption": "caption for image 2", "category": "category 1"},
            {"id": 3, "url": "./static/images/3.jpg", "caption": "caption for image 3", "category": "category 1"},
            {"id": 4, "url": "./static/images/4.jpg", "caption": "caption for image 4", "category": "category 1"},
            {"id": 5, "url": "./static/images/5.jpg", "caption": "caption for image 5", "category": "category 1"},
            {"id": 6, "url": "./static/images/6.jpg", "caption": "caption for image 6", "category": "category 1"},
            {"id": 7, "url": "./static/images/7.jpg", "caption": "caption for image 7", "category": "category 1"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "caption for image 8", "category": "category 1"},
        ]
    else:
        # Log the error
        app.logger.error(f"Failed to get images: {response}")
        return []

def get_saved_images(username):
    # Use TCP client to fetch saved images
    success, response = tcp_client.send_request("GET_SAVED_IMAGES", {"username": username})
    
    if success:
        # In a real implementation, response would contain the saved images
        # For now, return the static list
        return [
            {"id": 1, "url": "./static/images/9.jpg", "caption": "caption for image 1", "category": "category 1"},
            {"id": 2, "url": "./static/images/10.jpg", "caption": "caption for image 2", "category": "category 1"},
            {"id": 3, "url": "./static/images/11.jpg", "caption": "caption for image 3", "category": "category 1"},
            {"id": 4, "url": "./static/images/8.jpg", "caption": "caption for image 4", "category": "category 1"}
        ]
    else:
        # Log the error
        app.logger.error(f"Failed to get saved images: {response}")
        return []

#home page
@app.route('/home')
def index():
    images = get_homepage_images()
    return render_template('index.html', images=images)

#login page
@app.route('/')
def login():
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
    
    if success:
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error="Login failed")

#saved page 
@app.route('/saved')
def saved():
    username = "TestUser"
    images = get_saved_images(username)
    return render_template('saved-section.html', images=images, username=username)

#profile page
@app.route('/profile')
def profile():
    username = "TestUser"
    return render_template('profile.html', username=username)

#image uploads
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'no file (flask side)', 400
    #gets info from form
    image = request.files['image']
    caption = request.form.get('caption')
    tags = request.form.get('tags')
    
    #handles case where no file is selected
    if image.filename == '':
        return 'empty string, no selected file', 400
    
    #temporary for testing until we send info to server
    return jsonify({
        'filename': image.filename,
        'caption': caption,
        'tags': tags
    })




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