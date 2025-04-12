
import base64
import os
import json


class ImageManager:
    def __init__(self, upload_folder='./static/uploads', saved_images_file='saved_images.json', uploaded_images_file='images.json'):
        self.upload_folder = upload_folder
        self.saved_images_file = saved_images_file
        self.uploaded_images_file = uploaded_images_file
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        self.uploaded_images = []
        self.saved_images = {}
        self.load_saved_images()
        self.load_uploaded_images()

    def load_uploaded_images(self):
        if os.path.exists(self.uploaded_images_file):
            with open(self.uploaded_images_file, 'r') as f:
                self.uploaded_images = json.load(f)
        else:
            self.uploaded_images = []

    def save_uploaded_images(self):
        with open(self.uploaded_images_file, 'w') as f:
            json.dump(self.uploaded_images, f, indent=4)

    def upload_image(self, image_file, caption, tags):
        #handles case where no file is selected
        if image_file.filename == '':
            return None, 'No selected file'
        
        #need to encode the image to base64 to be able to actually send it
        #find info here: https://docs.python.org/3/library/base64.html
        image_content = image_file.read()
        base64_image = base64.b64encode(image_content).decode('utf-8')

        #store the image in the folder (since database is not ready yet)
        from werkzeug.utils import secure_filename
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(self.upload_folder, image_filename)

        with open(image_path, 'wb') as f:
            f.write(image_content)
        
        #new image dictionary for the users newly uploaded image
        uploaded_image = {
            'id': len(self.uploaded_images) + 1, 
            'url': f"/static/uploads/{image_filename}",
            'caption': caption,
            'category': tags
        }

        #store in file  (while db not up)
        self.uploaded_images.append(uploaded_image)
        self.save_uploaded_images()

        #return image details for success
        return uploaded_image, None
    
    def get_images(self):
        #when database is ready, this will be to get from the database instead
        return self.uploaded_images
    
    
    def load_saved_images(self):
        if os.path.exists(self.saved_images_file):
            with open(self.saved_images_file, 'r') as f:
                self.saved_images = json.load(f)
        else:
            self.saved_images = {}

    def save_saved_images(self):
        with open(self.saved_images_file, 'w') as f:
            json.dump(self.saved_images, f, indent=4)
     
    
    def get_saved_images(self, username):
        return self.saved_images.get(username, [])

    #find and return the image by its ID
    def get_image_by_id(self, image_id):
        images = self.get_images()
        for image in images:
            print(image['id'])
            if image['id'] == int(image_id):
                return image
        return None

    def save_image_for_user(self, image, username):
       if username not in self.saved_images:
            self.saved_images[username] = []

        #dont double save an image, so check is not already saved
       if not any(saved_image['id'] == int(image['id']) for saved_image in self.saved_images[username]):
            self.saved_images[username].append(image)
            self.save_saved_images()