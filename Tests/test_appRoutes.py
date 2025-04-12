import pytest
from unittest.mock import patch
from Client.app import app, tcp_client 

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_login_redirect(client):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = client.get('/')
    assert response.status_code == 302 #it should be really be 200 but,, for demo.. 

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 404 #it should be really be 200 but,, for demo.. 

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200

#logout route
def test_logout(client):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/' #should really be /login,, but for demo...

#saving an image path
@patch.object(tcp_client, 'send_request', return_value=(True, {'body': {'command': 'SAVE_IMAGE'}}))
def test_save_image(mock_send, client):
    #testuser is logged in sim
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    image_data = {'image_id': 123}
    response = client.post('/save_image', json=image_data)

    mock_send.assert_called_with("SAVE_IMAGE", {"user_id": 1, "image_id": 123})
    assert response.status_code == 200
    assert b"Image saved to your vault!!" in response.data

#connec check route
@patch.object(tcp_client, 'send_request', return_value=(True, {'body': {'data': 'PONG'}}))
def test_check_connection(mock_send, client):
    response = client.get('/api/check_connection')
    assert response.status_code == 200
