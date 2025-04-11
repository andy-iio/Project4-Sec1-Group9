from flask import Flask, render_template, request, jsonify, send_from_directory
import threading
import os
import logging
from tcp_server import TCPServer

# Create a separate logger for the Flask app
flask_logger = logging.getLogger('FlaskApp')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - FlaskApp - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
flask_logger.addHandler(handler)
flask_logger.setLevel(logging.INFO)

app = Flask(__name__)
app.logger.handlers = []  

# Initialize the socket server
socket_server = None
tcp_log_file = 'server_log.txt'

@app.route('/')
def index():
    return render_template('servergui.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/start_server', methods=['POST'])
def start_server_route():
    global socket_server
    
    if socket_server is not None and socket_server.running:
        return jsonify({"status": "warning", "message": "Server is already running"})
    
    try:
        # Clear the log file before starting the server
        with open(tcp_log_file, 'w') as f:
            f.write("TCP Server starting...\n")
            
        start_socket_server()
        flask_logger.info("TCP Server started via web interface")
        return jsonify({"status": "success", "message": "Server started successfully"})
    except Exception as e:
        flask_logger.error(f"Error starting TCP server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/stop_server', methods=['POST'])
def stop_server_route():
    global socket_server
    
    if socket_server is None or not socket_server.running:
        return jsonify({"status": "warning", "message": "Server is not running"})
    
    try:
        socket_server.stop()
        socket_server = None
        flask_logger.info("TCP Server stopped via web interface")
        return jsonify({"status": "success", "message": "Server stopped successfully"})
    except Exception as e:
        flask_logger.error(f"Error stopping TCP server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_logs')
def get_logs():
    logs = []
    
    try:
        if os.path.exists(tcp_log_file):
            with open(tcp_log_file, 'r') as f:
                all_logs = f.readlines()
                
                # Filter out logs related to /get_logs requests
                logs = [log.strip() for log in all_logs 
                       if 'GET /get_logs' not in log and '/static/server.css' not in log]
                
                # Get the last 20 logs after filtering
                logs = logs[-20:] if len(logs) > 20 else logs
    except Exception as e:
        logs = [f"Error reading logs: {str(e)}"]
    
    return jsonify({"logs": logs})

def start_socket_server():
    """Start the TCP server in a separate thread"""
    global socket_server
    
    # Initialize the server
    socket_server = TCPServer(port=5001)
    
    # Start the server in a new thread
    server_thread = threading.Thread(target=socket_server.start)
    server_thread.daemon = True
    server_thread.start()

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
    
    app.run(debug=True, host='0.0.0.0', port=5000)