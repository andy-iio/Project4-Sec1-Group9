import socket
import json
import threading
import logging
import hashlib
import time
from datetime import datetime
from database import PreppersDB  
# Set up logging
logging.basicConfig(
    filename='server_log.txt',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TCPServer')

class TCPServerConnection:
    """
    Handles an individual client connection to the server
    """
    
    def __init__(self, client_socket, address, db):
        """Initialize the connection handler"""
        self.client_socket = client_socket
        self.address = address
        self.sequence_number = 0
        self.db = db
        
    def calculate_checksum(self, data):
        """Calculate checksum for data"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def validate_checksum(self, data, checksum):
        """Validate the checksum matches the data"""
        return self.calculate_checksum(data) == checksum
    
    def handle_request(self):
        """Handle client requests"""
        try:
            logger.info(f"Connection established with {self.address}")
            
            # Main request handling loop
            while True:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                logger.info(f"Received data from {self.address}: {data[:100]}...")
                
                try:
                    # Parse the received packet
                    packet = json.loads(data)
                    
                    # Log packet header details
                    if 'header' in packet:
                        logger.info(f"Request from {self.address}: Source={packet['header'].get('source')}, "
                                    f"Command={packet['body'].get('command') if 'body' in packet else 'unknown'}")
                    
                    # Validate header
                    if 'header' not in packet:
                        self.send_error("Invalid packet format - missing header")
                        continue
                        
                    # Validate checksum
                    if 'footer' in packet and 'checksum' in packet['footer']:
                        if not self.validate_checksum(json.dumps(packet['body']), packet['footer']['checksum']):
                            logger.warning(f"Checksum validation failed for request from {self.address}")
                            self.send_error("Checksum validation failed")
                            continue
                    else:
                        logger.warning(f"Missing checksum in request from {self.address}")
                        self.send_error("Missing checksum")
                        continue
                    
                    # Process the command
                    command = packet['body'].get('command', '')
                    data = packet['body'].get('data', {})
                    
                    # Handle different command types
                    response_data = self.process_command(command, data)
                    
                    # Create and send response
                    response = self.create_packet(response_data['command'], response_data['data'])
                    self.client_socket.sendall(json.dumps(response).encode('utf-8'))
                    logger.info(f"Sent response to {self.address}: {response_data['command']}")
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON format from {self.address}")
                    self.send_error("Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing request from {self.address}: {str(e)}")
                    self.send_error(f"Error processing request: {str(e)}")
                
        except Exception as e:
            logger.error(f"Connection error with {self.address}: {str(e)}")
        finally:
            self.client_socket.close()
            logger.info(f"Connection closed with {self.address}")
    
    def process_command(self, command, data):
        """Process the request command and return response data"""
        # Default response
        response = {
            "command": "ERROR",
            "data": {"message": "Unknown command"}
        }
        
        # Handle different commands
        if command == "PING":
            response = {
                "command": "PONG",
                "data": {
                    "received_timestamp": data.get("timestamp", 0),
                    "server_timestamp": time.time()
                }
            }
        
        elif command == "TEST" or command == "ECHO":
            response = {
                "command": "ECHO",
                "data": {
                    "message": "Server received your request",
                    "original_command": command,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        elif command == "LOGIN":
            username = data.get("username", "")
            password = data.get("password", "")
            
            success, user_id = self.db.authenticate_user(username, password)
            
            if success:
                response = {
                    "command": "LOGIN_SUCCESS",
                    "data": {
                        "user_id": user_id,
                        "username": username
                    }
                }
            else:
                response = {
                    "command": "LOGIN_FAILED",
                    "data": {
                        "message": "Invalid username or password"
                    }
                }
        
        elif command == "REGISTER":
            username = data.get("username", "")
            password = data.get("password", "")
            email = data.get("email", None)
            
            success, result = self.db.add_user(username, password, email)
            
            if success:
                response = {
                    "command": "REGISTER_SUCCESS",
                    "data": {
                        "user_id": result,
                        "username": username
                    }
                }
            else:
                response = {
                    "command": "REGISTER_FAILED",
                    "data": {
                        "message": result
                    }
                }
        
        elif command == "UPLOAD_IMAGE":
            filename = data.get("filename", "")
            caption = data.get("caption", "")
            tags = data.get("tags", "")
            user_id = data.get("user_id", None)
            image_data = data.get("image", None)
            
            if not user_id:
                response = {
                    "command": "UPLOAD_FAILED",
                    "data": {
                        "message": "User ID is required"
                    }
                }
            else:
                success, image_id = self.db.save_image(filename, caption, tags, user_id, image_data)
                
                if success:
                    response = {
                        "command": "UPLOAD_SUCCESS",
                        "data": {
                            "image_id": image_id,
                            "filename": filename
                        }
                    }
                else:
                    response = {
                        "command": "UPLOAD_FAILED",
                        "data": {
                            "message": image_id  # Error message
                        }
                    }
        
        elif command == "GET_IMAGES":
            images = self.db.get_images(limit=20)
            
            response = {
                "command": "IMAGES",
                "data": {
                    "images": images
                }
            }
        
        elif command == "GET_SAVED_IMAGES":
            user_id = data.get("user_id", None)
            
            if not user_id:
                response = {
                    "command": "GET_SAVED_FAILED",
                    "data": {
                        "message": "User ID is required"
                    }
                }
            else:
                images = self.db.get_user_saved_images(user_id)
                
                response = {
                    "command": "SAVED_IMAGES",
                    "data": {
                        "images": images
                    }
                }
        
        elif command == "SAVE_IMAGE":
            user_id = data.get("user_id", None)
            image_id = data.get("image_id", None)
            
            if not user_id or not image_id:
                response = {
                    "command": "SAVE_IMAGE_FAILED",
                    "data": {
                        "message": "User ID and Image ID are required"
                    }
                }
            else:
                success, result = self.db.save_image_for_user(user_id, image_id)
                
                if success:
                    response = {
                        "command": "SAVE_IMAGE_SUCCESS",
                        "data": {
                            "user_id": user_id,
                            "image_id": image_id
                        }
                    }
                else:
                    response = {
                        "command": "SAVE_IMAGE_FAILED",
                        "data": {
                            "message": result
                        }
                    }
        
        elif command == "UNSAVE_IMAGE":
            user_id = data.get("user_id", None)
            image_id = data.get("image_id", None)
            
            if not user_id or not image_id:
                response = {
                    "command": "UNSAVE_IMAGE_FAILED",
                    "data": {
                        "message": "User ID and Image ID are required"
                    }
                }
            else:
                success = self.db.unsave_image_for_user(user_id, image_id)
                
                response = {
                    "command": "UNSAVE_IMAGE_SUCCESS",
                    "data": {
                        "user_id": user_id,
                        "image_id": image_id,
                        "success": success
                    }
                }
                
        return response
    
    def send_error(self, message):
        """Send error message back to client"""
        response = self.create_packet("ERROR", {"message": message})
        self.client_socket.sendall(json.dumps(response).encode('utf-8'))
        logger.info(f"Error sent to {self.address}: {message}")
    
    def create_packet(self, command, data):
        """Create a response packet"""
        self.sequence_number += 1
        
        body = {
            "command": command,
            "data": data
        }
        
        body_json = json.dumps(body)
        checksum = self.calculate_checksum(body_json)
        
        packet = {
            "header": {
                "source": "SERVER",
                "destination": "CLIENT",
                "size": len(body_json),
                "sequence_number": self.sequence_number
            },
            "body": body,
            "footer": {
                "checksum": checksum
            }
        }
        
        return packet


class TCPServer:
    """
    TCP/IP Socket server
    """
    
    def __init__(self, host='0.0.0.0', port=5001, db=None):
        """Initialize the socket server"""
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        self.db = db
        
    def start(self):
        """Start the server"""
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Allow port reuse
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the port
            self.server_socket.bind((self.host, self.port))
            
            # Listen for connections
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Server started on {self.host}:{self.port}")
            
            # Accept connections
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                
                # Create client handler with database access
                client_handler = TCPServerConnection(client_socket, client_address, self.db)
                
                # Start a thread to handle the client
                client_thread = threading.Thread(target=client_handler.handle_request)
                client_thread.daemon = True
                client_thread.start()
                
                self.clients.append(client_thread)
                
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Server stopped")


if __name__ == "__main__":
    # This is just for testing 
    from database import PreppersDB
    
    # Initialize database
    db = PreppersDB()
    
    # Start the server
    server = TCPServer(port=5001, db=db)
    server.start()