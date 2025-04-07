import base64
import os
import json


class ImageManager:
    def __init__(self, upload_folder='./static/uploads', saved_images_file='saved_images.json'):
        self.upload_folder = upload_folder
        self.saved_images_file = saved_images_file
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        self.load_saved_images()


    def upload_image(self, image_file, caption, tags):
        #handles case where no file is selected
        if image_file.filename == '':
            return None, 'No selected file'
        
        #need to encode the image to base64 to be able to actually send it
        #find info here: https://docs.python.org/3/library/base64.html
        image_content = image_file.read()
        base64_image = base64.b64encode(image_content).decode('utf-8')

        #store the image in the folder (since database is not ready yet)
        image_filename = image_file.filename
        image_path = os.path.join(self.upload_folder, image_filename)

        with open(image_path, 'wb') as f:
            f.write(image_content)
        
        #return image details for success
        return {
            'filename': image_filename,
            'caption': caption,
            'tags': tags,
            'image': base64_image
        }, None
    
    def get_images(self):
        #to get from the database (database not set up yet tho?)
        return [
            {"id": 1, "url": "./static/images/1.jpg", "caption": "Best Survival Tools for Preppers", "category": "Tools"},
            {"id": 2, "url": "./static/images/2.jpg", "caption": "Prepare for Food Shortages", "category": "Meal Prep"},
            {"id": 3, "url": "./static/images/3.jpg", "caption": "Amazing Survival Recipes", "category": "Meal Prep"},
            {"id": 4, "url": "./static/images/4.jpg", "caption": "YOU NEED TO KNOW THESE LIFE HACKS!", "category": "Hacks"},
            {"id": 5, "url": "./static/images/5.jpg", "caption": "Your emergency stockpile isnt complete without these 100 things", "category": "Tools"},
            {"id": 6, "url": "./static/images/6.jpg", "caption": "World War 3 is COming, are you Prepared??", "category": "Tips"},
            {"id": 7, "url": "./static/images/7.jpg", "caption": "Want to Survive? Better read this..", "category": "Tips"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "Clothes that Guarentee Survival", "category": "Clothes"},
            {"id": 9, "url": "./static/images/9.jpg", "caption": "If you don'T have these in your pantry, uh oh", "category": "Meal Prep"},
            {"id": 10, "url": "./static/images/10.jpg", "caption": "Rebuild after the apocalypse is over with these plants", "category": "Gardening"},
            {"id": 11, "url": "./static/images/11.jpg", "caption": "Flowers will be worth millions soon, enjoy them now", "category": "Gardening"},
        ]
    
    
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