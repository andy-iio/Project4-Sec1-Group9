from Client.tcp_client import TCPClient

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash

import time
import base64
import os

from datetime import datetime
from Client.database import Database

app = Flask(__name__)
app.secret_key = os.urandom(24)  
app.secret_key = os.urandom(24)  

tcp_client = TCPClient(server_host='localhost', server_port=5001)


# comment_manager = CommentManager()
# image_manager = ImageManager()

upload_images = []
db = Database()


@app.route('/')
def login():
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', None)
        
        if not username or not password:
            return render_template('register.html', error="Username and password are required")
        
        success, result = db.create_user(username, password, email)
        
        if success:
            tcp_client.send_request("REGISTER", {
                "username": username,
                "user_id": result
            })
            
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=result)
    
    return render_template('register.html')

@app.route('/process_login', methods=['POST'])
def process_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('login.html', error="Username and password are required")
    
    success, user_id = db.authenticate_user(username, password)
    
    if success:
        session['user_id'] = user_id
        session['username'] = username
        
        tcp_client.send_request("LOGIN", {
            "username": username,
            "user_id": user_id
        })
        
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error="Invalid username or password")

@app.route('/logout')
def logout():
    if 'username' in session:
        tcp_client.send_request("LOGOUT", {
            "username": session['username'],
            "user_id": session['user_id']
        })
        
    session.pop('user_id', None)
    session.pop('username', None)
    
    return redirect(url_for('login'))

@app.route('/home')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    images = db.get_all_images()
    user = db.get_user(session['user_id'])
    
    # Mark images as saved or not
    for image in images:
        image['is_saved'] = db.is_image_saved_by_user(session['user_id'], image['id'])
    
    # Get unique categories for filtering
    categories = []
    for image in images:
        if image['category'] and image['category'] not in categories:
            categories.append(image['category'])
    
    return render_template('index.html', images=images, user=user, categories=categories)

@app.route('/saved')
def saved():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    images = db.get_saved_images(session['user_id'])
    user = db.get_user(session['user_id'])
    
    # Get unique categories for filtering
    categories = []
    for image in images:
        if image['category'] and image['category'] not in categories:
            categories.append(image['category'])
    
    return render_template('saved-section.html', images=images, username=user['username'], categories=categories)

@app.route('/save_image', methods=['POST'])
def save_image():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "You must be logged in to save images"})
    
    image_id = request.json.get('image_id')
    
    success = db.save_image_for_user(session['user_id'], image_id)
    
    if success:
        tcp_client.send_request("SAVE_IMAGE", {
            "user_id": session['user_id'],
            "image_id": image_id
        })
        
        return jsonify({"success": True, "message": "Image saved to your vault!!"})
    else:
        return jsonify({"success": False, "message": "Image already saved or couldn't be saved"})

@app.route('/unsave_image', methods=['POST'])
def unsave_image():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "You must be logged in to unsave images"})
    
    image_id = request.json.get('image_id')
    
    success = db.unsave_image_for_user(session['user_id'], image_id)
    
    if success:
        # Notify TCP server
        tcp_client.send_request("UNSAVE_IMAGE", {
            "user_id": session['user_id'],
            "image_id": image_id
        })
        
        return jsonify({"success": True, "message": "Image removed from your saved posts"})
    else:
        return jsonify({"success": False, "message": "Failed to remove image"})

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.get_user(session['user_id'])
    
    # Get counts for user stats
    saved_count = db.get_saved_count(session['user_id'])
    uploaded_count = db.get_uploaded_count(session['user_id'])
    comment_count = db.get_comment_count(session['user_id'])
    
    return render_template('profile.html', 
                          user=user, 
                          saved_count=saved_count,
                          uploaded_count=uploaded_count,
                          comment_count=comment_count)

# New route for viewing other user profiles
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """View another user's profile"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the requested user
    user = db.get_user(user_id)
    
    # If user doesn't exist, redirect to home
    if not user:
        flash("User not found", "error")
        return redirect(url_for('index'))
    
    # Get stats for the user
    saved_count = db.get_saved_count(user_id)
    uploaded_count = db.get_uploaded_count(user_id)
    comment_count = db.get_comment_count(user_id)
    
    return render_template('user-profile.html', 
                          user=user, 
                          saved_count=saved_count,
                          uploaded_count=uploaded_count,
                          comment_count=comment_count)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'image' not in request.files:
        return 'No file provided', 400
    
    image = request.files['image']
    caption = request.form.get('caption')
    tags = request.form.get('tags')
    
    if image.filename == '':
        return 'No selected file', 400
    
    # Save the file to uploads folder
    image_content = image.read()
    image_filename = image.filename
    upload_folder = './static/uploads'
    
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    image_path = os.path.join(upload_folder, image_filename)
    
    with open(image_path, 'wb') as f:
        f.write(image_content)
    
    # Encode image to base64 
    base64_image = base64.b64encode(image_content).decode('utf-8')
    
    # Save to database
    image_url = f"./static/uploads/{image_filename}"
    image_id = db.upload_image(image_url, caption, tags, session['user_id'], base64_image)
    
    # Notify TCP server
    image_data = {
        "id": image_id,
        "url": image_url,
        "caption": caption,
        "category": tags,
        "user_id": session['user_id'],
        "image": base64_image
    }
    
    tcp_client.send_request("UPLOAD_IMAGE", image_data)
    
    return redirect(url_for('index'))

@app.route('/api/comments/<int:image_id>')
def get_comments_for_img(image_id):
    comments = db.get_comments(image_id)
    return jsonify({"success": True, "comments": comments})

@app.route('/api/comments', methods=['POST'])
def save_comment():
   
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "You must be logged in to comment"})
    
    data = request.json
    if not data or 'imageId' not in data or 'text' not in data:
        return jsonify({"success": False, "message": "Fill out all required fields"})

    image_id = data['imageId']
    comment_text = data['text']

    success = db.add_comment(image_id, comment_text, session['user_id'])
    
    if success:
        
        tcp_client.send_request("ADD_COMMENT", {
            "user_id": session['user_id'],
            "image_id": image_id,
            "text": comment_text
        })
        
        return jsonify({"success": True, "message": "Comment posted!!"})
    else:
        return jsonify({"success": False, "message": "Failed to post comment"})

@app.route('/search')
def search():
    """
    Search for posts or users
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '')
    search_type = request.args.get('type', 'posts')  # Default to posts search
    
    if not query:
        # If no query, redirect back to the page the user came from or home
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        return redirect(url_for('index'))
    
    # Local database search
    if search_type == 'users':
        # Search for users
        results = db.search_users(query)
        
        # Also search with TCP server if connected
        if tcp_client.connected:
            try:
                success, tcp_results = tcp_client.search(query, "users")
                if success:
                    # Merge results, avoiding duplicates
                    existing_ids = [user['id'] for user in results]
                    for user in tcp_results:
                        if user['id'] not in existing_ids:
                            results.append(user)
            except Exception as e:
                print(f"Error searching users via TCP: {str(e)}")
        
        return render_template('search-results.html', 
                            query=query, 
                            search_type=search_type,
                            users=results)
    else:
        # Search for posts
        results = db.search_images(query, session['user_id'])
        
        # Also search with TCP server if connected
        if tcp_client.connected:
            try:
                success, tcp_results = tcp_client.search(query, "posts", session['user_id'])
                if success:
                    # Merge results, avoiding duplicates
                    existing_ids = [image['id'] for image in results]
                    for image in tcp_results:
                        if image['id'] not in existing_ids:
                            # Make sure to check if the image is saved by the current user
                            if 'is_saved' not in image:
                                image['is_saved'] = db.is_image_saved_by_user(session['user_id'], image['id'])
                            results.append(image)
            except Exception as e:
                print(f"Error searching posts via TCP: {str(e)}")
        
        # Get categories for filter buttons
        categories = []
        for image in results:
            if image['category'] and image['category'] not in categories:
                categories.append(image['category'])
        
        return render_template('search-results.html', 
                            query=query,
                            search_type=search_type,
                            images=results,
                            categories=categories)

@app.route('/api/check_connection')
def check_connection():
    if not tcp_client.connected:
        if not tcp_client.connect():
            return jsonify({"status": "disconnected", "message": "Failed to connect to server"})
    
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
    
    app.run(debug=True, port=5002)