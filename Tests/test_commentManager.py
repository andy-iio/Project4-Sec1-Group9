import os
import pytest
from Client.comment_manager import CommentManager 

TEST_FILE = 'test_comments.json'

@pytest.fixture(scope="module")
def comment_manager():
    cm = CommentManager(comments_file=TEST_FILE)
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    return cm

def test_load_comments_empty(comment_manager):
    comments = comment_manager.load_comments()
    assert comments == {}

def test_load_comments_from_file(comment_manager):
    mock_data = {
        '1': [{'text': 'nice bunker!', 'timestamp': '2023-04-10 10:00:00'}],
        '2': [{'text': 'wow!', 'timestamp': '2023-04-10 11:00:00'}]
    }
    comment_manager.save_comments(mock_data)
    comments = comment_manager.load_comments()
    
    assert comments == mock_data

def test_get_comments_for_image(comment_manager):

    mock_data = {
        '1': [{'text': 'wow', 'timestamp': '2025-04-10 10:00:00'}],
        '2': [{'text': 'cool', 'timestamp': '2025-04-10 11:00:00'}]
    }
    comment_manager.save_comments(mock_data)
    
    comments = comment_manager.get_comments('1')
    assert comments == mock_data['1']
    
    comments = comment_manager.get_comments('2')
    assert comments == mock_data['2']

def test_save_comment_new_image(comment_manager):
    image_id = '3'
    comment = "holy moly"

    result = comment_manager.save_comment(image_id, comment)
    
    assert result == {"success": True, "message": "comment posted!!"}
    comments = comment_manager.load_comments()
    assert str(image_id) in comments
    assert len(comments[str(image_id)]) == 1
    assert comments[str(image_id)][0]['text'] == comment
    assert 'timestamp' in comments[str(image_id)][0]

def test_save_comment_existing_image(comment_manager):
    image_id = '1'
    comment = "wow"
    
    initial_comments = {
        '1': [{'text': 'cool', 'timestamp': '2025-04-10 10:00:00'}]
    }
    comment_manager.save_comments(initial_comments)
    
    result = comment_manager.save_comment(image_id, comment)
    assert result == {"success": True, "message": "comment posted!!"}
    
    comments = comment_manager.load_comments()
    assert len(comments[str(image_id)]) == 2
    assert comments[str(image_id)][1]['text'] == comment
    assert 'timestamp' in comments[str(image_id)][1]

def test_save_comments_to_file(comment_manager):
    mock_data = {
        '1': [{'text': 'wow', 'timestamp': '2025-04-10 10:00:00'}],
        '2': [{'text': 'cool', 'timestamp': '2025-04-10 11:00:00'}]
    }
    
    comment_manager.save_comments(mock_data)
    comments = comment_manager.load_comments()
    
    assert comments == mock_data

def test_file_not_found_handling(comment_manager):
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    
    comments = comment_manager.load_comments()
    assert comments == {}
