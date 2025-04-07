import base64
import os

class ImageManager:
    def __init__(self, upload_folder='./static/uploads'):
        self.upload_folder = upload_folder
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

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
            {"id": 1, "url": "./static/images/1.jpg", "caption": "Best Survival Tools for Preppers", "category": "category 1"},
            {"id": 2, "url": "./static/images/2.jpg", "caption": "Prepare for Food Shortages", "category": "category 1"},
            {"id": 3, "url": "./static/images/3.jpg", "caption": "Amazing Survival Recipes", "category": "category 1"},
            {"id": 4, "url": "./static/images/4.jpg", "caption": "YOU NEED TO KNOW THESE LIFE HACKS!", "category": "category 1"},
            {"id": 5, "url": "./static/images/5.jpg", "caption": "Your emergency stockpile isnt complete without these 100 things", "category": "category 1"},
            {"id": 6, "url": "./static/images/6.jpg", "caption": "World War 3 is COming, are you Prepared??", "category": "category 1"},
            {"id": 7, "url": "./static/images/7.jpg", "caption": "Want to Survive? Better read this..", "category": "category 1"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "Clothes that Guarentee Survival", "category": "category 1"},
        ]
    
    def get_saved_images(self, username):
        return [
            {"id": 1, "url": "./static/images/9.jpg", "caption": "If you don'T have these in your pantry, uh oh", "category": "category 1"},
            {"id": 2, "url": "./static/images/10.jpg", "caption": "Rebuild after the apocalypse is over with these plants", "category": "category 1"},
            {"id": 3, "url": "./static/images/11.jpg", "caption": "Flowers will be worth millions soon, enjoy them now", "category": "category 1"},
            {"id": 8, "url": "./static/images/8.jpg", "caption": "Clothes that Guarentee Survival", "category": "category 1"},
        ]
