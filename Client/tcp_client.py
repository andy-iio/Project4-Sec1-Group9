import socket
import json
import logging
import hashlib
import time


# Logging structure for btoh clent and server
logging.basicConfig( 
    filename='client_log.txt',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - TCPClient - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TCPClient')
#this should get rid of the repetivite loh ruquests in gui
class FilterStaticRequests(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if '/static/' in record.msg or 'GET /static' in record.msg or 'GET /get_logs' in record.msg:
                return False
        return True

logger.addFilter(FilterStaticRequests())

class TCPClient:
    def __init__(self, server_host='localhost', server_port=5001):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.sequence_number = 0
        self.current_user = None
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            
            self.socket.connect((self.server_host, self.server_port))
            logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self): # pragma: no cover
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        logger.info("Disconnected from server")
    
    def send_request(self, command, data):
        if not self.connected:
            if not self.connect():
                return False, "Failed to connect to server"
                
        # Create request packet
        packet = self.create_packet(command, data)
        #ALL NAMING FUNCTIONS THAT SERVER SHOULD CALL
        try:
            packet_json = json.dumps(packet)
            self.socket.sendall(packet_json.encode('utf-8'))
            
            user_info = ""
            if command == "LOGIN" and data.get('username'):
                self.current_user = data.get('username')
                user_info = f"[User: {self.current_user}] "
            elif self.current_user and command != "LOGOUT":
                user_info = f"[User: {self.current_user}] "
            
            logger.info(f"{user_info}SENDING REQUEST: Command={command}")
            
            if command in ["LOGIN", "REGISTER", "LOGOUT", "SAVE_IMAGE", "UNSAVE_IMAGE", "UPLOAD_IMAGE", "ADD_COMMENT", "SEARCH"]:
                if command == "LOGIN":
                    logger.info(f"Login attempt for user '{data.get('username')}'")
                elif command == "REGISTER":
                    logger.info(f"Registering new user '{data.get('username')}'")
                elif command == "LOGOUT":
                    logger.info(f"User '{self.current_user}' logging out")
                    self.current_user = None
                elif command == "SAVE_IMAGE":
                    logger.info(f"User '{self.current_user}' saving image ID: {data.get('image_id')}")
                elif command == "UNSAVE_IMAGE":
                    logger.info(f"User '{self.current_user}' removing saved image ID: {data.get('image_id')}")
                elif command == "UPLOAD_IMAGE":
                    logger.info(f"User '{self.current_user}' uploading image: {data.get('caption')}")
                elif command == "ADD_COMMENT":
                    logger.info(f"User '{self.current_user}' adding comment to image ID: {data.get('image_id')}")
                elif command == "SEARCH":
                    logger.info(f"User '{self.current_user}' searching for '{data.get('query')}' (Type: {data.get('type', 'posts')})")
            
            response = self.receive_response()
            
            if response:
                logger.info(f"{user_info}RECEIVED RESPONSE: {response['body']['command']}")
                return True, response
            else:
                logger.warning("No response received from server")
                return False, "No response from server"
                
        except Exception as e:
            logger.error(f"Error sending request: {str(e)}")
            self.disconnect()
            return False, str(e)
    
    def create_packet(self, command, data):
        self.sequence_number += 1
        
        body = {
            "command": command,
            "data": data
        }
        
        body_json = json.dumps(body)
        checksum = self.calculate_checksum(body_json)
        
        packet = {
            "header": {
                "source": "CLIENT",
                "destination": "SERVER",
                "size": len(body_json),
                "sequence_number": self.sequence_number
            },
            "body": body,
            "footer": {
                "checksum": checksum
            }
        }
        
        return packet
    
    def calculate_checksum(self, data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def validate_checksum(self, data, checksum):
        return self.calculate_checksum(data) == checksum
    
    def receive_response(self, timeout=10):
        self.socket.settimeout(timeout)
        
        try:
            data = self.socket.recv(8192).decode('utf-8')
            if not data:
                logger.warning("Received empty response from server")
                return None
                
           
            response = json.loads(data)
            
            # Validate header
            if 'header' not in response:
                logger.warning("Invalid response format - missing header")
                return None
                
            # Validate checksum
            if 'footer' in response and 'checksum' in response['footer']:
                if not self.validate_checksum(json.dumps(response['body']), response['footer']['checksum']):
                    logger.warning("Response checksum validation failed")
                    return None
            else:
                logger.warning("Missing checksum in server response")
                return None
                
            return response
                
        except socket.timeout:
            logger.warning("Timeout waiting for server response")
            return None
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in server response")
            return None
        except Exception as e:
            logger.error(f"Error receiving response: {str(e)}")
            return None
    
    # searching posts and users
    def search(self, query, search_type="posts", user_id=None):
        """
        Search for posts or users
        """
        search_data = {
            "query": query,
            "type": search_type
        }
        
        if user_id:
            search_data["user_id"] = user_id
        
        logger.info(f"Performing search: '{query}' (Type: {search_type})")
        success, response = self.send_request("SEARCH", search_data)
        
        if success and response and 'body' in response and 'data' in response['body']:
            results = response['body']['data'].get('results', [])
            logger.info(f"Search returned {len(results)} results")
            return True, results
        else:
            logger.warning(f"Search failed for '{query}'")
            return False, []
    
    # UPDATED saving images
    def save_image(self, image_id, user_id):
        """
        Save an image to the user's vault
        """
        save_data = {
            "image_id": image_id,
            "user_id": user_id
        }
        
        logger.info(f"Saving image: ID={image_id} for user ID={user_id}")
        success, response = self.send_request("SAVE_IMAGE", save_data)
        
        if success and response and 'body' in response:
            command = response['body'].get('command', '')
            if command == "SAVE_IMAGE_SUCCESS":
                logger.info(f"Image {image_id} saved successfully")
                return True, "Image saved to vault"
            else:
                logger.warning(f"Save image failed: {response['body'].get('data', {}).get('message', 'Unknown error')}")
                return False, response['body'].get('data', {}).get('message', "Failed to save image")
        else:
            logger.warning(f"Failed to save image {image_id}")
            return False, "Communication error"
    
    # UPDATED LOGIC for unsaving images
    def unsave_image(self, image_id, user_id):
        """
        Remove an image from the user's vault
        """
        unsave_data = {
            "image_id": image_id,
            "user_id": user_id
        }
        
        logger.info(f"Removing saved image: ID={image_id} for user ID={user_id}")
        success, response = self.send_request("UNSAVE_IMAGE", unsave_data)
        
        if success and response and 'body' in response:
            command = response['body'].get('command', '')
            if command == "UNSAVE_IMAGE_SUCCESS":
                logger.info(f"Image {image_id} removed from saved")
                return True, "Image removed from vault"
            else:
                logger.warning(f"Unsave image failed: {response['body'].get('data', {}).get('message', 'Unknown error')}")
                return False, response['body'].get('data', {}).get('message', "Failed to remove image")
        else:
            logger.warning(f"Failed to unsave image {image_id}")
            return False, "Communication error"
    
