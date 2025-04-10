from flask import Flask
import threading
from tcp_server import TCPServer

app = Flask(__name__)

# Initialize the socket server
socket_server = None

@app.route('/')
def index():
    return 'If you see this its working! TCP Server is running in the background.'

def start_socket_server():
    """Start the TCP server in a separate thread"""
    global socket_server
    
    # Start the server
    socket_server = TCPServer(port=5001)
    socket_server.start()

# Start the socket server in a background thread
if __name__ == '__main__':
    # Start the socket server in a separate thread
    print("\n")
    print("#" * 70)
    print("STARTING TCP SERVER ON PORT 5001")
    print("#" * 70)
    
    server_thread = threading.Thread(target=start_socket_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("\n")
    print("#" * 70)
    print("STARTING SERVER APP")
    print("SERVER URL: http://127.0.0.1:5000")
    print("SERVER URL: http://localhost:5000")
    print("#" * 70)
    print("\n")
    
    # Run the Flask app
    app.run(debug=True)