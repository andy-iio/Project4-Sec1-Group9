import socket
import json
import threading
import logging
import hashlib
import time
import sys
import os
from datetime import datetime

logging.basicConfig(
    filename='server_log.txt',
    filemode='a',  
    level=logging.INFO,
    format='%(asctime)s - TCPServer - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TCPServer')

class ImprovedLogFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_error_time = 0
        self.error_count = 0
        self.last_error_msg = None
        
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if 'GET /get_logs' in record.msg or '/static/' in record.msg or ('GET /' in record.msg and 'ERROR' not in record.msg):
                return False
            
            if record.levelno >= logging.ERROR:
                current_time = time.time()
                error_msg = record.getMessage()
                
                if error_msg == self.last_error_msg:
                    if current_time - self.last_error_time > 5:
                        self.error_count = 0
                    
                    self.error_count += 1
                    self.last_error_time = current_time
                    
                    if self.error_count > 1:
                        return False
                else:
                    self.error_count = 1
                    self.last_error_msg = error_msg
                    self.last_error_time = current_time
                    
        return True

logger.addFilter(ImprovedLogFilter())

class TCPServerConnection:
    def __init__(self, client_socket, address, db):
        self.client_socket = client_socket
        self.address = address
        self.sequence_number = 0
        self.db = db
        self.username = None
        
    def calculate_checksum(self, data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def validate_checksum(self, data, checksum):
        return self.calculate_checksum(data) == checksum
    
    def handle_request(self):
        try:
            logger.info(f"Connection established with {self.address}")
            buffer = ""
            
            while True:
                try:
                    data = self.client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    
                    try:
                        packet = json.loads(buffer)
                        buffer = ""  
                        
                        if 'body' in packet and 'command' in packet['body'] and packet['body']['command'] == 'UPLOAD_IMAGE':
                            command = packet['body'].get('command')
                            data = packet['body'].get('data', {})
                            
                            user_info = f" [User: {self.username}]" if self.username else ""
                            logger.info(f"Processing image upload from {self.address}{user_info}")
                            
                            response_data = self.process_command(command, data)
                            response = self.create_packet(response_data["command"], response_data["data"])
                            
                            response_json = json.dumps(response)
                            self.client_socket.sendall(response_json.encode('utf-8'))
                            continue
                        
                        if 'header' in packet and 'body' in packet and 'command' in packet['body']:
                            cmd = packet['body']['command']
                            seq = packet['header'].get('sequence_number', 'unknown')
                            
                            if cmd == "LOGIN" and 'data' in packet['body'] and 'username' in packet['body']['data']:
                                self.username = packet['body']['data']['username']
                            
                            user_info = f" [User: {self.username}]" if self.username else ""
                            logger.info(f"REQUEST from {self.address}{user_info}: Command={cmd}, Sequence={seq}")
                            
                            command = packet['body'].get('command')
                            data = packet['body'].get('data', {})
                            
                            if command == "LOGOUT":
                                logger.info(f"User logged out: {self.username}")
                                self.username = None
                            
                            response_data = self.process_command(command, data)
                            
                            user_info = f" [User: {self.username}]" if self.username else ""
                            logger.info(f"Successfully processed command '{command}' from {self.address}{user_info}")
                            
                            response = self.create_packet(response_data["command"], response_data["data"])
                            response_json = json.dumps(response)
                            self.client_socket.sendall(response_json.encode('utf-8'))
                    
                    except json.JSONDecodeError:
                        if len(buffer) > 1024 * 1024:
                            if "UPLOAD_IMAGE" in buffer:
                                logger.info(f"Large image upload from {self.address}")
                                success_response = self.create_packet("UPLOAD_SUCCESS", {"message": "Image received"})
                                self.client_socket.sendall(json.dumps(success_response).encode('utf-8'))
                            
                            buffer = ""
                            logger.error(f"Buffer overflow from {self.address}, likely during image upload")
                    
                except UnicodeDecodeError:
                    logger.info(f"Received binary data from {self.address}, likely image upload")
                    buffer = ""
                    success_response = self.create_packet("UPLOAD_SUCCESS", {"message": "Data received"})
                    self.client_socket.sendall(json.dumps(success_response).encode('utf-8'))
                
                except Exception as e:
                    logger.error(f"Error processing request from {self.address}: {str(e)}")
                    self.send_error(f"Processing error")
                    buffer = ""
                    
        except Exception as e:
            logger.error(f"Connection error with {self.address}: {str(e)}")
        finally:
            self.client_socket.close()
            user_info = f" [User: {self.username}]" if self.username else ""
            logger.info(f"Connection closed with {self.address}{user_info}")
    
    def process_command(self, command, data):
        user_info = f" [User: {self.username}]" if self.username else ""
        
        command_log_messages = {
            "LOGIN": f"User login attempt: {data.get('username', '')}",
            "REGISTER": f"New user registration: {data.get('username', '')}",
            "UPLOAD_IMAGE": f"{user_info} Image upload - Caption: {data.get('caption', '')[:30]}... Category: {data.get('category', '')}",
            "SAVE_IMAGE": f"{user_info} Saved image ID: {data.get('image_id', '')}",
            "UNSAVE_IMAGE": f"{user_info} Removed saved image ID: {data.get('image_id', '')}",
            "ADD_COMMENT": f"{user_info} Added comment to image ID: {data.get('image_id', '')} - Text: {data.get('text', '')[:30]}...",
            "SEARCH": f"{user_info} Search - Query: {data.get('query', '')}, Type: {data.get('type', 'posts')}"
        }
        
        if command in command_log_messages:
            logger.info(command_log_messages[command])
        
        response = {
            "command": "ERROR",
            "data": {"message": "Unknown command"}
        }
        
        if command == "PING":
            response = {
                "command": "PONG",
                "data": {
                    "received_timestamp": data.get("timestamp", 0),
                    "server_timestamp": time.time()
                }
            }
        
        elif command in ["TEST", "ECHO"]:
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
            user_id = data.get("user_id", "")
            
            if user_id:
                response = {
                    "command": "LOGIN_SUCCESS",
                    "data": {
                        "user_id": user_id,
                        "username": username
                    }
                }
                logger.info(f"User logged in via ID: {username} (ID: {user_id})")
            else:
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
                    logger.info(f"User authenticated and logged in: {username} (ID: {user_id})")
                else:
                    response = {
                        "command": "LOGIN_FAILED",
                        "data": {
                            "message": "Invalid username or password"
                        }
                    }
                    logger.warning(f"Failed login attempt for user: {username}")
        
        elif command == "REGISTER":
            username = data.get("username", "")
            user_id = data.get("user_id", "")
            
            if user_id:
                response = {
                    "command": "REGISTER_SUCCESS",
                    "data": {
                        "user_id": user_id,
                        "username": username
                    }
                }
                logger.info(f"User registered via ID: {username} (ID: {user_id})")
            else:
                password = data.get("password", "")
                email = data.get("email", None)
                
                success, result = self.db.create_user(username, password, email)
                
                if success:
                    response = {
                        "command": "REGISTER_SUCCESS",
                        "data": {
                            "user_id": result,
                            "username": username
                        }
                    }
                    logger.info(f"New user registered: {username} (ID: {result})")
                else:
                    response = {
                        "command": "REGISTER_FAILED",
                        "data": {
                            "message": result
                        }
                    }
                    logger.warning(f"Failed registration attempt for username: {username} - {result}")
        
        elif command == "UPLOAD_IMAGE":
            image_id = data.get("id", None)
            url = data.get("url", "")
            caption = data.get("caption", "")
            category = data.get("category", "")
            user_id = data.get("user_id", None)
            image_data = data.get("image", None)
            
            if image_id:
                response = {
                    "command": "UPLOAD_SUCCESS",
                    "data": {
                        "image_id": image_id,
                        "url": url
                    }
                }
                logger.info(f"Image uploaded via ID: {image_id}, Caption: {caption}")
            else:
                if not user_id:
                    response = {
                        "command": "UPLOAD_FAILED",
                        "data": {
                            "message": "User ID is required"
                        }
                    }
                    logger.warning(f"Image upload failed: No user ID provided")
                else:
                    if url.startswith('./'):
                        url = url[1:]  
                        
                    image_id = self.db.upload_image(url, caption, category, user_id, image_data)
                    
                    if image_id:
                        response = {
                            "command": "UPLOAD_SUCCESS",
                            "data": {
                                "image_id": image_id,
                                "url": url
                            }
                        }
                        logger.info(f"Image uploaded successfully: ID={image_id}, Caption={caption}, User={user_id}")
                    else:
                        response = {
                            "command": "UPLOAD_FAILED",
                            "data": {
                                "message": "Failed to save image to database"
                            }
                        }
                        logger.error(f"Failed to save image to database: Caption={caption}, User={user_id}")
        
        elif command == "GET_IMAGES":
            images = self.db.get_all_images()
            
            response = {
                "command": "IMAGES",
                "data": {
                    "images": images
                }
            }
            logger.info(f"Returned {len(images)} images to {self.address}")
        
        elif command == "GET_SAVED_IMAGES":
            user_id = data.get("user_id", None)
            
            if not user_id:
                response = {
                    "command": "GET_SAVED_FAILED",
                    "data": {
                        "message": "User ID is required"
                    }
                }
                logger.warning(f"Get saved images failed: No user ID provided")
            else:
                images = self.db.get_saved_images(user_id)
                
                response = {
                    "command": "SAVED_IMAGES",
                    "data": {
                        "images": images
                    }
                }
                logger.info(f"Returned {len(images)} saved images for user ID: {user_id}")
        
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
                logger.warning(f"Save image failed: Missing required fields - User: {user_id}, Image: {image_id}")
            else:
                success = self.db.save_image_for_user(user_id, image_id)
                
                if success:
                    response = {
                        "command": "SAVE_IMAGE_SUCCESS",
                        "data": {
                            "user_id": user_id,
                            "image_id": image_id
                        }
                    }
                    logger.info(f"Image saved successfully: User={user_id}, Image={image_id}")
                else:
                    response = {
                        "command": "SAVE_IMAGE_FAILED",
                        "data": {
                            "message": "Image already saved or couldn't be saved"
                        }
                    }
                    logger.warning(f"Failed to save image (likely already saved): User={user_id}, Image={image_id}")
        
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
                logger.warning(f"Unsave image failed: Missing required fields - User: {user_id}, Image: {image_id}")
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
                logger.info(f"Image unsaved: User={user_id}, Image={image_id}, Success={success}")
        
        elif command == "SEARCH":
            query = data.get("query", "")
            search_type = data.get("type", "posts")
            user_id = data.get("user_id", None)
            
            if not query:
                response = {
                    "command": "SEARCH_FAILED",
                    "data": {
                        "message": "Search query is required"
                    }
                }
                logger.warning(f"Search failed: No query provided")
            else:
                if search_type == "users":
                    users = self.db.search_users(query)
                    response = {
                        "command": "SEARCH_RESULTS",
                        "data": {
                            "type": "users",
                            "query": query,
                            "results": users
                        }
                    }
                    logger.info(f"User search: Query='{query}', Results={len(users)}")
                else:
                    images = self.db.search_images(query, user_id)
                    response = {
                        "command": "SEARCH_RESULTS",
                        "data": {
                            "type": "posts",
                            "query": query,
                            "results": images
                        }
                    }
                    logger.info(f"Image search: Query='{query}', Results={len(images)}")
                
        return response
    
    def send_error(self, message):
        response = self.create_packet("ERROR", {"message": message})
        self.client_socket.sendall(json.dumps(response).encode('utf-8'))
        user_info = f" [User: {self.username}]" if self.username else ""
        logger.info(f"Error sent to {self.address}{user_info}: {message}")
    
    def create_packet(self, command, data):
        self.sequence_number += 1
        
        body = {"command": command, "data": data}
        body_json = json.dumps(body)
        checksum = self.calculate_checksum(body_json)
        
        return {
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


class TCPServer:
    def __init__(self, host='0.0.0.0', port=5001, db=None):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        self.db = db
        
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Server started on {self.host}:{self.port}")
            
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"New client connected: {client_address}")
                
                client_handler = TCPServerConnection(client_socket, client_address, self.db)
                
                client_thread = threading.Thread(target=client_handler.handle_request)
                client_thread.daemon = True
                client_thread.start()
                
                self.clients.append(client_thread)
                
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Server stopped")


if __name__ == "__main__":
    from database import Database
    
    print("\n")
    print("#" * 70)
    print("STARTING TCP SERVER ON PORT 5001")
    print("#" * 70)
    print("Log messages will be saved to server_log.txt")
    print("#" * 70)
    
    db = Database()
    server = TCPServer(port=5001, db=db)
    server.start()