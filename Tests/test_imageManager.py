import os
import pytest
from Client.image_manager import ImageManager

#empty folder struct for testing
#setup stuff
@pytest.fixture
def image_manager():
    manager = ImageManager(upload_folder="./test_uploads",saved_images_file="./test_saved_images.json",uploaded_images_file="./test_uploaded_images.json")
    
    #make sure folder exists
    if not os.path.exists(manager.upload_folder):
        os.makedirs(manager.upload_folder)
    
    #clear previous saved images/uploaded images before running tests
    manager.uploaded_images = []
    manager.saved_images = {}
    manager.save_uploaded_images()
    manager.save_saved_images()
    
    yield manager

    #clean up after
    if os.path.exists(manager.upload_folder):
        for f in os.listdir(manager.upload_folder):
            os.remove(os.path.join(manager.upload_folder, f))
        os.rmdir(manager.upload_folder)
    if os.path.exists(manager.saved_images_file):
        os.remove(manager.saved_images_file)
    if os.path.exists(manager.uploaded_images_file):
        os.remove(manager.uploaded_images_file)


def test_init(image_manager):
    assert os.path.exists(image_manager.upload_folder)  #folder exists
    assert isinstance(image_manager.uploaded_images, list)  #uploaded_images is a list
    assert isinstance(image_manager.saved_images, dict)  #saved_images should is a dictionary


def test_upload_image(image_manager):
    #temp file creation
    with open("./test_uploads/test_image.jpg", "wb") as f:
        f.write(b"test_image_data")
    
    class ImageFile:
        def __init__(self, filename):
            self.filename = filename
            self.content = open(f"./test_uploads/{filename}", "rb").read()
        
        def read(self):
            return self.content
    
    test_image_file = ImageFile("test_image.jpg")
    caption = "Cool Bunker Decor"
    tags = ["bunker"]

    uploaded_image, error = image_manager.upload_image(test_image_file, caption, tags)

    assert uploaded_image is not None
    assert uploaded_image['caption'] == caption
    assert uploaded_image['category'] == tags
    assert uploaded_image['image'] == "dGVzdF9pbWFnZV9kYXRh"  # base64 
    assert error is None
    assert os.path.exists(os.path.join(image_manager.upload_folder, "test_image.jpg"))  #check that it was actually written to the folder


def test_get_images(image_manager):
    #sample image
    image_manager.uploaded_images.append({
        'id': 1,
        'url': './test_uploads/test_image.jpg',
        'caption': 'test image',
        'category': ['test'],
        'image': 'test_base64'
    })
    
    #check matches
    images = image_manager.get_images()
    assert len(images) == 1
    assert images[0]['caption'] == 'test image'


def test_save_and_get_saved_images(image_manager):
    image = {
        'id': 1,
        'url': './test_uploads/test_image.jpg',
        'caption': 'saved image',
        'category': ['test'],
        'image': 'saved_base64'
    }
    
    username = "test_user"
    image_manager.save_image_for_user(image, username)
    saved_images = image_manager.get_saved_images(username)
    
    assert len(saved_images) == 1
    assert saved_images[0]['caption'] == 'saved image'


def test_get_image_by_id(image_manager):
    image_manager.uploaded_images.append({
        'id': 1,
        'url': './test_uploads/test_image.jpg',
        'caption': 'test image',
        'category': ['test'],
        'image': 'test_base64'
    })
    image = image_manager.get_image_by_id(1)
    assert image is not None
    assert image['caption'] == 'test image'


def test_get_image_by_id_doesnt_exist(image_manager):
    image_manager.uploaded_images.append({
        'id': 1,
        'url': './test_uploads/test_image.jpg',
        'caption': 'Test Image',
        'category': ['test'],
        'image': 'test_base64'
    })
     
    #try one thats not there
    image = image_manager.get_image_by_id(999)
    assert image is None