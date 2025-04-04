import socket
import json
import logging
import hashlib
import time

# Logging structure
logging.basicConfig(
    filename='client_log.txt',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TCPClient')

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
    
    def disconnect(self):
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
            logger.info(f"Sent request: {command} with {len(packet_json)} bytes")
            
            # Wait for response
            response = self.receive_response()
            
            if response:
                logger.info(f"Received response: {response['body']['command']}")
                return True, response
            else:
                logger.warning("No response from server")
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
                
            # Parse response
            response = json.loads(data)
            
            # Valid8 header
            if 'header' not in response:
                logger.warning("Invalid response format - missing header")
                return None
                
            # Valid8 checksum
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

# Example ( testing)
if __name__ == "__main__":
    # Create client
    client = TCPClient()
    
    # Connect to server
    if not client.connect():
        print("Failed to connect to server")
        exit(1)
    
    # Send a test request
    success, response = client.send_request("TEST", {
        "message": "Hello, server!",
        "timestamp": time.time()
    })
    
    if success:
        print("Request successful!")
        print(f"Response: {response['body']['data'].get('message', 'No message')}")
    else:
        print(f"Request failed: {response}")
    
   
    client.disconnect()