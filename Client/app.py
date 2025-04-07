from flask import Flask, render_template, request, jsonify, redirect, url_for
from tcp_client import TCPClient
import time
import base64

from comment_manager import CommentManager

app = Flask(__name__)

# Create a global client instance
tcp_client = TCPClient(server_host='localhost', server_port=5001)

#comment manager instance
comment_manager = CommentManager()

upload_images = []
#temporary for now, we will need to set up the getting of images through the server
def get_homepage_images():
    # Use TCP client to fetch images
    success, response = tcp_client.send_request("GET_IMAGES", {})
    
    if success:
        # In a real implementation, response would contain the images
        # For now, return the static list
        default_images = [
            {"id": 1, "url": "./static/images/1.jpg", "caption": "Best Survival Tools for Preppers", "category": "category 1"},
            {"id": 2, "url": "./static/images/2.jpg", "caption": "Prepare for Food Shortages", "category": "category 1"},
            {"id": 3, "url": "./static/images/3.jpg", "caption": "Amazing Survival Recipes", "category": "category 1"},
            {"id": 4, "url": "./static/images/4.jpg", "caption": "YOU NEED TO KNOW THESE LIFE HACKS!", "category": "category 1"},
            {"id": 5, "url": "./static/images/5.jpg", "caption": "Your emergency stockpile isnt complete without these 100 things", "category": "category 1"},
            {"id": 6, "url": "./static/images/6.jpg", "caption": "World War 3 is COming, are you Prepared??", "category": "category 1"},
            {"id": 7, "url": "./static/images/7.jpg", "caption": "Want to Survive? Better read this..", "category": "category 1"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "Clothes that Guarentee Survival", "category": "category 1"},
        ]

        return upload_images + default_images
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
            {"id": 1, "url": "./static/images/9.jpg", "caption": "If you don'T have these in your pantry, uh oh", "category": "category 1"},
            {"id": 2, "url": "./static/images/10.jpg", "caption": "Rebuild after the apocalypse is over with these plants", "category": "category 1"},
            {"id": 3, "url": "./static/images/11.jpg", "caption": "Flowers will be worth millions soon, enjoy them now", "category": "category 1"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "Clothes that Guarentee Survival", "category": "category 1"},
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
    username = "Andy"
    images = get_saved_images(username)
    return render_template('saved-section.html', images=images, username=username)

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
    
    #handles case where no file is selected
    if image.filename == '':
        return 'empty string, no selected file', 400
    
    #need to encode the image to base64 to be able to actually send it
    #find info here: https://docs.python.org/3/library/base64.html
    image_content = image.read()
    base64_image = base64.b64encode(image_content).decode('utf-8')

    data = {
        'filename': image.filename,
        'caption': caption,
        'tags': tags,
        'image': base64_image
    }

    success, response = tcp_client.send_request("UPLOAD_IMAGE", data)

    if success:
        # upload_images.insert(0, {
        #     "id": 999, 
        #     "url": f"./static/uploads/{image.filename}", 
        #     "caption": caption,
        #     "category": "category"
        # })
        return redirect(url_for('index'))
        # return jsonify({
        #     'filename': image.filename,
        #     'caption': caption,
        #     'tags': tags
        # })
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