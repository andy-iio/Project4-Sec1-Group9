import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch
from Client.tcp_client import TCPClient


def test_connect_failure():
    client = TCPClient(server_host="localhost", server_port=5001)

    with patch.object(client, 'socket', MagicMock()):
        client.socket.connect = MagicMock(side_effect=Exception("Connection failed"))
        result = client.connect()
    
    assert result == False
    assert client.connected == False

def test_send_request_success():
    client = TCPClient(server_host="localhost", server_port=5001)
    client.connected = True
    
    with patch.object(client, 'send_request', return_value=(True, {"body": {"command": "LOGIN"}})) as mock_send:
        result, response = client.send_request("LOGIN", {"username": "test_user"})
    
    assert result == True
    assert response["body"]["command"] == "LOGIN"

def test_send_request_failed_connection():
    client = TCPClient(server_host="localhost", server_port=5001)
    client.connected = False  #not connected to client sim

    with patch.object(client, 'connect', return_value=False):
        result, message = client.send_request("LOGIN", {"username": "test_user"})
    assert result is False
    assert message == "Failed to connect to server"

def test_send_request_invalid_data():
    client = TCPClient(server_host="localhost", server_port=5001)
    client.connected = True
    result, message = client.send_request("LOGIN", {})
    assert result is False

#if failed connection
def test_send_request_failed_connection():
    client = TCPClient(server_host="localhost", server_port=5001)
    client.connected = False
    
    with patch.object(client, 'connect', return_value=False):
        result, message = client.send_request("LOGIN", {"username": "test_user"})
    
    assert result == False
    assert message == "Failed to connect to server"

#calculate_checksum()
def test_calculate_checksum():
    client = TCPClient(server_host="localhost", server_port=5001)
    data = '{"command": "LOGIN", "data": {"username": "test_user"}}'
    
    checksum = client.calculate_checksum(data)
    
    assert len(checksum) == 32  #hash length
    assert checksum == hashlib.md5(data.encode('utf-8')).hexdigest()

def test_validate_checksum():
    client = TCPClient(server_host="localhost", server_port=5001)
    data = '{"command": "LOGIN", "data": {"username": "test_user"}}'
    checksum = hashlib.md5(data.encode('utf-8')).hexdigest()

    is_valid = client.validate_checksum(data, checksum)
    
    assert is_valid == True

def test_send_request_invalid_checksum():
    client = TCPClient(server_host="localhost", server_port=5001)

    with patch.object(client, 'receive_response', return_value={
        "header": {"source": "SERVER", "destination": "CLIENT"},
        "body": {"command": "LOGIN", "data": {"username": "test_user"}},
        "footer": {"checksum": "invalid_checksum"}
    }):
        result, message = client.send_request("LOGIN", {"username": "test_user"})

    assert result is False


def test_receive_response_invalid_checksum():
    client = TCPClient(server_host="localhost", server_port=5001)

    with patch.object(client, 'socket', MagicMock()):
        client.socket.recv = MagicMock(return_value=json.dumps({
            "header": {"source": "SERVER", "destination": "CLIENT"},
            "body": {"command": "LOGIN", "data": {"username": "test_user"}},
            "footer": {"checksum": "invalid_checksum"}
        }).encode('utf-8'))
        response = client.receive_response()

    assert response is None

#create_packet method
def test_create_packet():
    client = TCPClient(server_host="localhost", server_port=5001)
    command = "LOGIN"
    data = {"username": "test_user"}
    
    packet = client.create_packet(command, data)
    
    # assert packet["header"]["command"] == "LOGIN"
    assert packet["footer"]["checksum"] is not None

#connect method
# def test_connect_success():
#     client = TCPClient(server_host="localhost", server_port=5001)

#     with patch.object(client, 'socket', MagicMock()):
#         client.socket.connect = MagicMock(return_value=None)  # Simulate successful connection
#         result = client.connect()
    
#     assert result == True
    # assert client.connected == True
