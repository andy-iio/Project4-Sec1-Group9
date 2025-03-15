from flask import Flask, render_template

app = Flask(__name__)

#temporary for now, we will need to set up the getting of images through the server
def get_homepage_images():
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

def get_saved_images(username):
    # call the server with the username

    #temporary static images
    return [
        {"id": 1, "url": "./static/images/9.jpg", "caption": "caption for image 1", "category": "category 1"},
        {"id": 2, "url": "./static/images/10.jpg", "caption": "caption for image 2", "category": "category 1"},
        {"id": 3, "url": "./static/images/11.jpg", "caption": "caption for image 3", "category": "category 1"},
        {"id": 4, "url": "./static/images/8.jpg", "caption": "caption for image 4", "category": "category 1"}
    ]

#home page
@app.route('/')
def index():
    images = get_homepage_images()
    return render_template('index.html', images=images)

#saved page 
@app.route('/saved')
def saved():
    username = "Username001"
    images = get_saved_images(username)
    return render_template('saved-section.html', images=images, username=username)

#profile page
@app.route('/profile')
def profile():
    username = "Username001"
    return render_template('profile.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)