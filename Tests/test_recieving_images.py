import pytest
from unittest.mock import MagicMock
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Image_Classifier.Image_Classifier.deployment import load_and_predict

# Mock server with only the logic needed for the test
class MockServer:
    def __init__(self):
        self.client_socket = MagicMock()
        self.address = ('127.0.0.1', 12345)

    #just a copy and paste from my file 
    #updated recieve_image function
    def receive_image(client_socket, filename, filesize):
        os.makedirs("Stored_Images", exist_ok=True)  # Ensure the directory exists
        save_path = os.path.join("Stored_Images", filename)  # Specify the path to save the file
        
        with open(save_path, 'wb') as f:  # Open the file in write-binary mode
            data = client_socket.recv(filesize)  # Receive image data
            f.write(data)  # Write the data to the file
            try:
                # Use the path where the image was saved
                model_path = os.path.join("Image_Classifier", "Image_Classifier", "imageclassiferHS_Updated.h5")
                predicted_class, _ = load_and_predict(model_path, save_path)

                print(f"Predicted Class: {predicted_class}")  # Debugging log
                logging.info(f"Predicted Class: {predicted_class}")  
                
                # Now that we have the predicted class, create the response data
                response_data = {
                    "status": "success",
                    "prediction": predicted_class,
                    "category": predicted_class  # Fix: Assign predicted class to category
                }
                
                return response_data
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def handle_packet(self, packet):
        try:
            command = packet['body']['command']
            if command == "UPLOAD_IMAGE":
                if 'filename' in packet['body'] and 'filesize' in packet['body']:
                    filename = packet['body']['filename']
                    filesize = packet['body']['filesize']
                    self.receive_image(self.client_socket, filename, filesize)
                else:
                    logging.info("Image not in the correct format")
        except Exception as e:
            logging.error(f"Connection error with {self.address}: {str(e)}")


# Actual pytest test functions (outside any class)
def test_upload_image_valid_packet(caplog):
    server = MockServer()
    server.receive_image = MagicMock()

    packet = {
        'body': {
            'command': 'UPLOAD_IMAGE',
            'filename': 'test.jpg',
            'filesize': 2048
        }
    }

    server.handle_packet(packet)
    server.receive_image.assert_called_once_with(server.client_socket, 'test.jpg', 2048)


def test_upload_image_missing_fields(caplog):
    server = MockServer()
    server.receive_image = MagicMock()

    # Set log level to capture INFO logs
    caplog.set_level(logging.INFO)

    packet = {
        'body': {
            'command': 'UPLOAD_IMAGE'
        }
    }

    server.handle_packet(packet)

    server.receive_image.assert_not_called()

    assert "Image not in the correct format" in caplog.text


    server.handle_packet(packet)

    # Make sure receive_image is NOT called
    server.receive_image.assert_not_called()

    # And we should have a log message
    assert "Image not in the correct format" in caplog.text
