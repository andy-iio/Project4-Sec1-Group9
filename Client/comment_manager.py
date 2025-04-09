import os
import json
from datetime import datetime

#just using a file, its easier, we can change to database if time
COMMENTS_FILE = 'comments.json'

class CommentManager:
    def __init__(self, comments_file=COMMENTS_FILE):
        self.comments_file = comments_file

    
    # load up comments from the file
    def load_comments(self):
        if os.path.exists(self.comments_file):
            try:
                with open(self.comments_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    # save the comments to the file
    def save_comments(self, comments):
        with open(self.comments_file, 'w') as f:
            json.dump(comments, f)

    # get the comments for a specific image 
    def get_comments(self, image_id):
        comments_data = self.load_comments()
        return comments_data.get(str(image_id), [])
    
    #save the new comment for a specific image
    def save_comment(self, image_id, comment): 
        comments_data = self.load_comments()
        
        if str(image_id) not in comments_data:
            comments_data[str(image_id)] = []
        
        #append it with a timestamp
        comments_data[image_id].append({
            "text": comment,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self.save_comments(comments_data)  
        return {"success": True, "message": "comment posted!!"}
