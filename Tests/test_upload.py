import sys
print(sys.path) 

from Client.app import app
from Client.tcp_client import TCPClient

def test_upload_image():
    assert app is not None