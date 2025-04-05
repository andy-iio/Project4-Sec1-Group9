import socket
import json
import threading
import logging
import hashlib
import time
from datetime import datetime

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
    Handles an individual client connection to the server lets goo
    """
    
    def __init__(self, client_socket, address):
        """Initialize the connection handler"""
        self.client_socket = client_socket
        self.address = address
        self.sequence_number = 0
        
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
                    
                    # Valid8 header
                    if 'header' not in packet:
                        self.send_error("Invalid packet format - missing header")
                        continue
                        
                    # Valid8 checksum
                    if 'footer' in packet and 'checksum' in packet['footer']:
                        if not self.validate_checksum(json.dumps(packet['body']), packet['footer']['checksum']):
                            logger.warning(f"Checksum validation failed for request from {self.address}")
                            self.send_error("Checksum validation failed")
                            continue
                    else:
                        logger.warning(f"Missing checksum in request from {self.address}")
                        self.send_error("Missing checksum")
                        continue
                    
                    # Echo the request back to the client (for testing)
                    echo_response = self.create_packet("ECHO", {
                        "message": "Server received your request",
                        "original_command": packet['body'].get('command', 'unknown'),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    self.client_socket.sendall(json.dumps(echo_response).encode('utf-8'))
                    logger.info(f"Sent echo response to {self.address}")
                    
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
    
    def send_error(self, message):
        """Send error message back to client"""
        response = self.create_packet("ERROR", {"message": message})
        self.client_socket.sendall(json.dumps(response).encode('utf-8'))
        logger.info(f"Error sent to {self.address}: {message}")
    
     #packet details? could change also need to add tls encyption
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
    
    def __init__(self, host='0.0.0.0', port=5001):
        """Initialize the socket server"""
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        
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
                
                # Create client handler
                client_handler = TCPServerConnection(client_socket, client_address)
                
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
    # Start the server
    server = TCPServer(port=5001)
    server.start()