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

# tried to add a filter to exclude static file requests from logs(kind of works)
class FilterStaticRequests(logging.Filter): # pragma: no cover
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if '/static/' in record.msg or 'GET /static' in record.msg:
                return False
        return True

logger.addFilter(FilterStaticRequests())

class TCPClient:
    """
    TCP/IP Socket client for communicating with the server
    """
    
    def __init__(self, server_host='localhost', server_port=5001):
        """Initialize the socket client"""
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.sequence_number = 0
        
    def connect(self):
        """Connect to the server"""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to the server
            self.socket.connect((self.server_host, self.server_port))
            logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self): # pragma: no cover
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
        self.connected = False
        logger.info("Disconnected from server")
    
    def send_request(self, command, data):
        """Send a request to the server"""
        if not self.connected:
            if not self.connect():
                return False, "Failed to connect to server"
                
        # Create request packet
        packet = self.create_packet(command, data)
        
        # Send request
        try:
            packet_json = json.dumps(packet)
            self.socket.sendall(packet_json.encode('utf-8'))
            
         
            logger.info(f"SENDING REQUEST TO SERVER: Command={command}")
            
            # For important commands it will  log more details
            if command in ["LOGIN", "REGISTER", "LOGOUT", "SAVE_IMAGE", "UNSAVE_IMAGE", "UPLOAD_IMAGE", "ADD_COMMENT"]:
                if command == "LOGIN":
                    logger.info(f"User '{data.get('username')}' logging in")
                elif command == "REGISTER":
                    logger.info(f"New user '{data.get('username')}' registering")
                elif command == "LOGOUT":
                    logger.info(f"User logging out")
                elif command == "SAVE_IMAGE":
                    logger.info(f"Saving image ID: {data.get('image_id')}")
                elif command == "UNSAVE_IMAGE":
                    logger.info(f"Removing saved image ID: {data.get('image_id')}")
                elif command == "UPLOAD_IMAGE":
                    logger.info(f"Uploading new image with caption: {data.get('caption')}")
                elif command == "ADD_COMMENT":
                    logger.info(f"Adding comment to image ID: {data.get('image_id')}")
            
            # Wait for response from the server to then log it
            response = self.receive_response()
            
            if response:
                logger.info(f"RECEIVED RESPONSE FROM SERVER: {response['body']['command']}")
                return True, response
            else:
                logger.warning("No response received from server")
                return False, "No response from server"
                
        except Exception as e:
            logger.error(f"Error sending request: {str(e)}")
            # Try to reconnect on next request
            self.disconnect()
            return False, str(e)
    
    def create_packet(self, command, data):
        """Create a request packet"""
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
        """Calculate checksum for data"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def validate_checksum(self, data, checksum):
        """Validate the checksum matches the data"""
        return self.calculate_checksum(data) == checksum
    
    def receive_response(self, timeout=10):
        """Receive and parse a response from the server"""
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