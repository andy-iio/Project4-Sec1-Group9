import sqlite3
import os
import hashlib
import json
from datetime import datetime
import base64
import logging

# Set up logging
logging.basicConfig(
    filename='database_log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - Database - %(levelname)s - %(message)s'
)
db_logger = logging.getLogger('Database')

class Database:
    def __init__(self, db_name='preppersdb.sqlite'):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.init_db()
        
    def connect(self):
        self.connection = sqlite3.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row  
        self.cursor = self.connection.cursor()
        
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def commit(self):
        if self.connection:
            self.connection.commit()
    
    def log(self, message):
        print(f"[Database] {message}")
        db_logger.info(message)
    
    def init_db(self):
        self.connect()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                caption TEXT,
                category TEXT,
                user_id INTEGER,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                user_id INTEGER,
                text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS saved_images (
                user_id INTEGER NOT NULL,
                image_id INTEGER NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, image_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (image_id) REFERENCES images (id)
            )'''
        ]
        
        for table in tables:
            self.cursor.execute(table)
      
        self._create_default_user()
        
        self.cursor.execute("SELECT COUNT(*) FROM images WHERE is_default = 1")
        if self.cursor.fetchone()[0] == 0:
            self._insert_default_data()
            
        self._import_default_saved_images()
            
        self.commit()
        self.close()
        
    def _create_default_user(self):
        self.cursor.execute("SELECT id FROM users WHERE username = 'Andy'")
        user = self.cursor.fetchone()
        
        if not user:
            password_hash = hashlib.sha256('password'.encode()).hexdigest()
            
            self.cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                ('Andy', password_hash, 'andy@preppers.app')
            )
            
            self.log("INFO - Created default user 'Andy' with password 'password'")
        else:
            self.log("INFO - Default user 'Andy' already exists")
    
    def _insert_default_data(self):
        default_images = [
            (1, "/static/images/1.jpg", "Best Survival Tools for Preppers", "Tools", 1, 1),
            (2, "/static/images/2.jpg", "Prepare for Food Shortages", "Meal Prep", 1, 1),
            (3, "/static/images/3.jpg", "Amazing Survival Recipes", "Meal Prep", 1, 1),
            (4, "/static/images/4.jpg", "YOU NEED TO KNOW THESE LIFE HACKS!", "Hacks", 1, 1),
            (5, "/static/images/5.jpg", "Your emergency stockpile isnt complete without these 100 things", "Tools", 1, 1),
            (6, "/static/images/6.jpg", "World War 3 is Coming, are you Prepared??", "Tips", 1, 1),
            (7, "/static/images/7.jpg", "Want to Survive? Better read this..", "Tips", 1, 1),
            (8, "/static/images/8.jpg", "Clothes that Guarantee Survival", "Clothes", 1, 1),
            (9, "/static/images/9.jpg", "If you don'T have these in your pantry, uh oh", "Meal Prep", 1, 1),
            (10, "/static/images/10.jpg", "Rebuild after the apocalypse is over with these plants", "Gardening", 1, 1),
            (11, "/static/images/11.jpg", "Flowers will be worth millions soon, enjoy them now", "Gardening", 1, 1)
        ]
        
        self.cursor.executemany(
            'INSERT INTO images (id, url, caption, category, user_id, is_default) VALUES (?, ?, ?, ?, ?, ?)',
            default_images
        )
        
        self.log("INFO - Inserted default images")
            
        default_comments = [
            (2, "helped, my bunker is stocked now", "2025-04-05 20:19:05"),
            (2, "omg, can't wait to eat this", "2025-04-05 20:19:11"),
            (4, "Great hacks!", "2025-04-05 20:36:40"),
            (3, "I survived thanks to this post", "2025-04-05 20:36:57"),
            (8, "very stylish 10/10", "2025-04-05 21:00:31")
        ]
        
        self.cursor.executemany(
            'INSERT INTO comments (image_id, text, timestamp) VALUES (?, ?, ?)',
            default_comments
        )
                
        self.log("INFO - Inserted default comments")
    
    def _import_default_saved_images(self):
        self.cursor.execute("SELECT id FROM users WHERE username = 'Andy'")
        user = self.cursor.fetchone()
        
        if not user:
            self.log("WARNING - Cannot import saved images, Andy user not found")
            return
            
        user_id = user[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM saved_images WHERE user_id = ?", (user_id,))
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            self.log("INFO - Andy already has saved images, skipping import")
            return
            
        saved_images = [(user_id, 9), (user_id, 10), (user_id, 3)]
        
        self.cursor.executemany(
            'INSERT INTO saved_images (user_id, image_id) VALUES (?, ?)',
            saved_images
        )
            
        self.log(f"INFO - Imported {len(saved_images)} saved images for Andy")
    
    def create_user(self, username, password, email=None):
        """Create a new user"""
        self.connect()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            self.cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, password_hash, email)
            )
            self.commit()
            
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = self.cursor.fetchone()[0]
            
            self.log(f"INFO - Created new user: {username} (ID: {user_id})")
            self.close()
            return True, user_id
        except sqlite3.IntegrityError:
            self.log(f"WARNING - Username already exists: {username}")
            self.close()
            return False, "Username already exists"
        except Exception as e:
            self.log(f"ERROR - Failed to create user {username}: {str(e)}")
            self.close()
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Authenticate a user by username and password"""
        self.connect()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        
        user = self.cursor.fetchone()
        self.close()
        
        if user:
            self.log(f"INFO - User authenticated: {username}")
            return True, user[0]
        
        self.log(f"WARNING - Failed login attempt for user: {username}")
        return False, "Invalid username or password"
    
    def get_user(self, user_id):
        """Get user details by ID"""
        self.connect()
        
        self.cursor.execute(
            'SELECT id, username, email, created_at FROM users WHERE id = ?',
            (user_id,)
        )
        
        user = self.cursor.fetchone()
        self.close()
        
        if user:
            return dict(user)
        return None
    
    def get_all_images(self):
        """Get all images in the database"""
        self.connect()
        
        self.cursor.execute('''
        SELECT id, url, caption, category, user_id, is_default, created_at
        FROM images
        ORDER BY is_default DESC, id DESC
        ''')
        
        images = [dict(row) for row in self.cursor.fetchall()]
        
        for image in images:
            if image.get('url'):
                if image['url'].startswith('./static'):
                    image['url'] = image['url'][1:]
                elif not image['url'].startswith('/') and not image['url'].startswith('http'):
                    image['url'] = '/' + image['url']
        
        self.close()
        
        return images
    
    def get_image_by_id(self, image_id):
        """Get image details by ID"""
        self.connect()
        
        self.cursor.execute('''
        SELECT id, url, caption, category, user_id, is_default, created_at, image_data
        FROM images
        WHERE id = ?
        ''', (image_id,))
        
        image = self.cursor.fetchone()
        self.close()
        
        if image:
            image_dict = dict(image)
            
            if image_dict.get('url'):
                if image_dict['url'].startswith('./static'):
                    image_dict['url'] = image_dict['url'][1:]
                elif not image_dict['url'].startswith('/') and not image_dict['url'].startswith('http'):
                    image_dict['url'] = '/' + image_dict['url']
                    
            return image_dict
        return None
    
    def upload_image(self, url, caption, category, user_id=None, image_data=None):
        """Upload a new image"""
        self.connect()
        
        try:
            if url.startswith('./'):
                url = url[1:]
            elif not url.startswith('/') and not url.startswith('http'):
                url = '/' + url

            self.cursor.execute(
                'INSERT INTO images (url, caption, category, user_id, image_data) VALUES (?, ?, ?, ?, ?)',
                (url, caption, category, user_id, image_data)
            )
            
            image_id = self.cursor.lastrowid
            self.commit()
            
            # Log the upload
            username = None
            if user_id:
                self.cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                user = self.cursor.fetchone()
                if user:
                    username = user['username']
            
            self.log(f"INFO - Image uploaded: ID={image_id}, Caption={caption}, Category={category}, User={username or user_id}")
            
            self.close()
            return image_id
        except Exception as e:
            self.log(f"ERROR - Failed to upload image: {e}")
            self.close()
            return None
    
    def get_comments(self, image_id):
        """Get comments for a specific image with username"""
        self.connect()
        
        self.cursor.execute('''
        SELECT c.id, c.image_id, c.user_id, c.text, c.timestamp, u.username
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.image_id = ?
        ORDER BY c.timestamp DESC
        ''', (image_id,))
        
        comments = [dict(row) for row in self.cursor.fetchall()]
        self.close()
        
        return comments
    
    def add_comment(self, image_id, text, user_id=None):
        """Add a comment to an image with username"""
        self.connect()
        
        try:
            # Get username if user_id is provided
            username = None
            if user_id:
                self.cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                user = self.cursor.fetchone()
                if user:
                    username = user['username']
            
            self.cursor.execute(
                'INSERT INTO comments (image_id, user_id, text) VALUES (?, ?, ?)',
                (image_id, user_id, text)
            )
            
            comment_id = self.cursor.lastrowid
            self.commit()
            
            # Log the comment
            self.log(f"INFO - Comment added: ID={comment_id}, Image={image_id}, User={username or user_id}, Text={text[:30]}...")
            
            self.close()
            return True, comment_id, username
        except Exception as e:
            self.log(f"ERROR - Failed to add comment: {e}")
            self.close()
            return False, None, None
   
    def get_saved_images(self, user_id):
        """Get all images saved by a specific user"""
        self.connect()
        
        self.cursor.execute('''
        SELECT i.*
        FROM images i
        JOIN saved_images s ON i.id = s.image_id
        WHERE s.user_id = ?
        ORDER BY s.saved_at DESC
        ''', (user_id,))
        
        images = [dict(row) for row in self.cursor.fetchall()]
        
        for image in images:
            if image.get('url'):
                if image['url'].startswith('./static'):
                    image['url'] = image['url'][1:]
                elif not image['url'].startswith('/') and not image['url'].startswith('http'):
                    image['url'] = '/' + image['url']
            
            # Mark all images as saved since they're from the saved_images table
            image['is_saved'] = True
        
        self.close()
        
        return images
    
    def save_image_for_user(self, user_id, image_id):
        """Save an image for a user"""
        self.connect()
        
        try:
            self.cursor.execute(
                'INSERT INTO saved_images (user_id, image_id) VALUES (?, ?)',
                (user_id, image_id)
            )
            
            self.commit()
            
            # Get username for logging
            username = None
            self.cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = self.cursor.fetchone()
            if user:
                username = user['username']
                
            # Get image caption for logging
            caption = None
            self.cursor.execute('SELECT caption FROM images WHERE id = ?', (image_id,))
            image = self.cursor.fetchone()
            if image:
                caption = image['caption']
            
            self.log(f"INFO - Image saved: User={username or user_id}, Image={image_id}, Caption={caption}")
            
            self.close()
            return True
        except sqlite3.IntegrityError:
            self.log(f"WARNING - Image already saved: User={user_id}, Image={image_id}")
            self.close()
            return False
        except Exception as e:
            self.log(f"ERROR - Failed to save image: User={user_id}, Image={image_id}, Error={str(e)}")
            self.close()
            return False
    
    def is_image_saved_by_user(self, user_id, image_id):
        """Check if an image is saved by a specific user"""
        self.connect()
        
        self.cursor.execute(
            'SELECT 1 FROM saved_images WHERE user_id = ? AND image_id = ?',
            (user_id, image_id)
        )
        
        is_saved = self.cursor.fetchone() is not None
        self.close()
        
        return is_saved
        
    def unsave_image_for_user(self, user_id, image_id):
        """Remove a saved image for a user"""
        self.connect()
        
        try:
            # Get username and image info for logging before deletion
            username = None
            caption = None
            
            self.cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = self.cursor.fetchone()
            if user:
                username = user['username']
                
            self.cursor.execute('SELECT caption FROM images WHERE id = ?', (image_id,))
            image = self.cursor.fetchone()
            if image:
                caption = image['caption']
                
            # Now delete the saved image
            self.cursor.execute(
                'DELETE FROM saved_images WHERE user_id = ? AND image_id = ?',
                (user_id, image_id)
            )
            
            deleted = self.cursor.rowcount > 0
            self.commit()
            
            if deleted:
                self.log(f"INFO - Image unsaved: User={username or user_id}, Image={image_id}, Caption={caption}")
            else:
                self.log(f"WARNING - Image was not saved to begin with: User={username or user_id}, Image={image_id}")
            
            self.close()
            return True
        except Exception as e:
            self.log(f"ERROR - Failed to unsave image: User={user_id}, Image={image_id}, Error={str(e)}")
            self.close()
            return False

    def get_saved_count(self, user_id):
        """Get the count of saved images for a user"""
        self.connect()
        
        self.cursor.execute('SELECT COUNT(*) FROM saved_images WHERE user_id = ?', (user_id,))
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count

    def get_uploaded_count(self, user_id):
        """Get the count of images uploaded by a user"""
        self.connect()
        
        self.cursor.execute(
            'SELECT COUNT(*) FROM images WHERE user_id = ? AND is_default = 0',
            (user_id,)
        )
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count

    def get_comment_count(self, user_id):
        """Get the count of comments made by a user"""
        self.connect()
        
        self.cursor.execute('SELECT COUNT(*) FROM comments WHERE user_id = ?', (user_id,))
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count
        
    def search_images(self, query, user_id=None):
        """
        Search for images based on caption, category, or tags
        If user_id is provided, also mark whether each image is saved by the user
        """
        self.connect()
        
        try:
            search_term = f'%{query}%'
            
            self.cursor.execute('''
            SELECT id, url, caption, category, user_id, is_default, created_at
            FROM images
            WHERE caption LIKE ? OR category LIKE ?
            ORDER BY is_default DESC, id DESC
            ''', (search_term, search_term))
            
            images = [dict(row) for row in self.cursor.fetchall()]
            
            # Get username for logging 
            username = None
            if user_id:
                self.cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                user = self.cursor.fetchone()
                if user:
                    username = user['username']
            
            # Process images
            for image in images:
                if image.get('url'):
                    if image['url'].startswith('./static'):
                        image['url'] = image['url'][1:]
                    elif not image['url'].startswith('/') and not image['url'].startswith('http'):
                        image['url'] = '/' + image['url']
                
                # If user_id is provided, check if image is saved by user
                if user_id:
                    self.cursor.execute(
                        'SELECT 1 FROM saved_images WHERE user_id = ? AND image_id = ?',
                        (user_id, image['id'])
                    )
                    image['is_saved'] = self.cursor.fetchone() is not None
            
            # Log the search with the username we already retrieved
            self.log(f"INFO - Image search: Query='{query}', User={username or user_id}, Results={len(images)}")
            
            return images
        except Exception as e:
            self.log(f"ERROR - Failed to search images: {str(e)}")
            return []
        finally:
            self.close()

    def search_users(self, query):
        """
        Search for users based on username
        """
        self.connect()
        
        try:
            search_term = f'%{query}%'
            
            self.cursor.execute('''
            SELECT id, username, email, created_at
            FROM users
            WHERE username LIKE ?
            ''', (search_term,))
            
            users = [dict(row) for row in self.cursor.fetchall()]
            
            # Log the search
            self.log(f"INFO - User search: Query='{query}', Results={len(users)}")
            
            return users
        except Exception as e:
            self.log(f"ERROR - Failed to search users: {str(e)}")
            return []
        finally:
            self.close()