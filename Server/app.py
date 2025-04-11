from flask import Flask, render_template,jsonify
import threading
from tcp_server import TCPServer

app = Flask(__name__)

# Initialize the socket server
socket_server = None

@app.route('/')

def index():
    return render_template('serverGUI.html')

def start_socket_server():
    """Start the TCP server in a separate thread"""
    global socket_server

    # Start the server
    socket_server = TCPServer(port=5001)
    socket_server.start()

# The log file to read from
LOG_FILE = 'server_log.txt'

@app.route('/get_logs', methods=['GET'])
def get_logs():
    """Serve the logs to the frontend"""
    logs = read_logs()
    return jsonify(logs)

def read_logs():
    """Read the log file and return the last few lines"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = f.readlines()
        return logs[-10:]  # Return the last 10 lines of the log file
    except FileNotFoundError:
        return ["Log file not found."]

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