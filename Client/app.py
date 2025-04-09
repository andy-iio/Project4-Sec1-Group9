from flask import Flask, render_template, request, jsonify, redirect, url_for
from Client.tcp_client import TCPClient
import time
import base64

from comment_manager import CommentManager
from image_manager import ImageManager

app = Flask(__name__)

# Create a global client instance
tcp_client = TCPClient(server_host='localhost', server_port=5001)

#initialize the managers 
comment_manager = CommentManager()
image_manager = ImageManager()

upload_images = []

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
    
#home page
@app.route('/home')
def index():
    # Use TCP client to fetch images
    # success, response = tcp_client.send_request("GET_IMAGES", {})
    images = image_manager.get_images()
    return render_template('index.html', images=images)


#saved page 
@app.route('/saved')
def saved():
    # Use TCP client to fetch saved images
    # success, response = tcp_client.send_request("GET_SAVED_IMAGES", {"username": username})
    username = "Andy"
    images = image_manager.get_saved_images(username)
    return render_template('saved-section.html', images=images, username=username)

#when clicking the saved button on an image, copy it to the saved section
@app.route('/save_image', methods=['POST'])
def save_image():
    image_id = request.json.get('image_id')
    username = "Andy" 

    image = image_manager.get_image_by_id(image_id)
    if image:
        image_manager.save_image_for_user(image, username)
        return jsonify({"success": True, "message": "Image saved to your vault!!"})

    return jsonify({"success": False, "message": "Couldn't save this image. Please try again later"})

#profile page
@app.route('/profile')
def profile():
    username = "Andy"
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
    
    image_data, error = image_manager.upload_image(image, caption, tags)
    if error:
        return error, 400
    
    success, response = tcp_client.send_request("UPLOAD_IMAGE", image_data)
    if success:
        return redirect(url_for('index'))
    else:
        return jsonify({'status': 'error', 'message': response})

#comment handleing routes
#to get the comments for a specific post
@app.route('/api/comments/<int:image_id>')
def get_comments_for_img(image_id):
    image_comments = comment_manager.get_comments(image_id)
    return jsonify({"success": True, "comments": image_comments})

#save a newly written comment
@app.route('/api/comments', methods=['POST'])
def save_comment():
    data = request.json
    if not data or 'imageId' not in data or 'text' not in data:
        return jsonify({"success": False, "message": "fill out all required fields"})

    image_id = data['imageId']
    comment_text = data['text']
    
    result = comment_manager.save_comment(image_id, comment_text)
    
    return jsonify(result)


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