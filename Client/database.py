import sqlite3
import os
import hashlib
import json
from datetime import datetime
import base64

class Database:
    def __init__(self, db_name='preppersdb.sqlite'):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.init_db()
        
    def connect(self):
        """Connect to the SQLite database"""
        self.connection = sqlite3.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row  
        self.cursor = self.connection.cursor()
        
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def commit(self):
        """Commit changes to the database"""
        if self.connection:
            self.connection.commit()
    
    def log(self, message):
        """Simple logging function"""
        print(f"[Database] {message}")
    
    def init_db(self):
        """Initialize the database tables if they don't exist"""
        self.connect()
        
        # Database tables for all the commands and functions that will be used
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
                classification_label TEXT,
                classification_confidence REAL,
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
            )''',
            '''CREATE TABLE IF NOT EXISTS classification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images (id)
            )'''
        ]
        
        for table in tables:
            self.cursor.execute(table)
        
        try:
            self.cursor.execute("ALTER TABLE images ADD COLUMN classification_label TEXT")
            self.log("INFO - Added classification_label column to images table")
        except sqlite3.OperationalError:
           
            pass
            
        try:
            self.cursor.execute("ALTER TABLE images ADD COLUMN classification_confidence REAL")
            self.log("INFO - Added classification_confidence column to images table")
        except sqlite3.OperationalError:
            pass
      
        self._create_default_user()
        
        self.cursor.execute("SELECT COUNT(*) FROM images WHERE is_default = 1")
        if self.cursor.fetchone()[0] == 0:
            self._insert_default_data()
            
        # Import saved images
        self._import_default_saved_images()
            
        self.commit()
        self.close()
        
        
        #ACCOUNT ANDY IS USED FOR TESTING PURPOSE AND IS HARDOCDED INTO DATABSE SO TEH DEFAULT IMAGES CAN BE USED passowrd is the passwrod
        
        
    def _create_default_user(self):
        """Create a default 'Andy' user if it doesn't exist"""
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
        """Insert default images into the database"""
        # Default images 
        default_images = [
            (1, "./static/images/1.jpg", "Best Survival Tools for Preppers", "Tools", 1),
            (2, "./static/images/2.jpg", "Prepare for Food Shortages", "Meal Prep", 1),
            (3, "./static/images/3.jpg", "Amazing Survival Recipes", "Meal Prep", 1),
            (4, "./static/images/4.jpg", "YOU NEED TO KNOW THESE LIFE HACKS!", "Hacks", 1),
            (5, "./static/images/5.jpg", "Your emergency stockpile isnt complete without these 100 things", "Tools", 1),
            (6, "./static/images/6.jpg", "World War 3 is Coming, are you Prepared??", "Tips", 1),
            (7, "./static/images/7.jpg", "Want to Survive? Better read this..", "Tips", 1),
            (8, "./static/images/8.jpg", "Clothes that Guarantee Survival", "Clothes", 1),
            (9, "./static/images/9.jpg", "If you don'T have these in your pantry, uh oh", "Meal Prep", 1),
            (10, "./static/images/10.jpg", "Rebuild after the apocalypse is over with these plants", "Gardening", 1),
            (11, "./static/images/11.jpg", "Flowers will be worth millions soon, enjoy them now", "Gardening", 1)
        ]
        
        
        self.cursor.executemany(
            'INSERT INTO images (id, url, caption, category, user_id, is_default) VALUES (?, ?, ?, ?, ?, ?)',
            default_images
        )
        
        self.log("INFO - Inserted default images")
            
        # Insert default comments
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
        """Import Andy's saved images from the provided JSON data"""
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
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            self.cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, password_hash, email)
            )
            self.commit()
            
            # Get the user ID
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = self.cursor.fetchone()[0]
            
            self.close()
            return True, user_id
        except sqlite3.IntegrityError:
            self.close()
            return False, "Username already exists"
    
    def authenticate_user(self, username, password):
        """Authenticate a user"""
        self.connect()
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        
        user = self.cursor.fetchone()
        self.close()
        
        if user:
            return True, user[0]
        return False, "Invalid username or password"
    
    def get_user(self, user_id):
        """Get user by ID"""
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
        """Get all images (default + user uploaded)"""
        self.connect()
        
        self.cursor.execute('''
        SELECT id, url, caption, category, user_id, is_default, created_at, classification_label, classification_confidence
        FROM images
        ORDER BY is_default DESC, id DESC
        ''')
        
        images = [dict(row) for row in self.cursor.fetchall()]
        self.close()
        
        return images
    
    def get_image_by_id(self, image_id):
        """Get image by ID"""
        self.connect()
        
        self.cursor.execute('''
        SELECT id, url, caption, category, user_id, is_default, created_at, image_data, 
               classification_label, classification_confidence
        FROM images
        WHERE id = ?
        ''', (image_id,))
        
        image = self.cursor.fetchone()
        self.close()
        
        if image:
            return dict(image)
        return None
    
    def upload_image(self, url, caption, category, user_id=None, image_data=None, classification_label=None, classification_confidence=None):
        """Upload a new image with classification data"""
        self.connect()
        
        try:
            self.cursor.execute(
                'INSERT INTO images (url, caption, category, user_id, image_data, classification_label, classification_confidence) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (url, caption, category, user_id, image_data, classification_label, classification_confidence)
            )
            
            image_id = self.cursor.lastrowid
           
            if classification_label and classification_confidence is not None:
                self.cursor.execute(
                    'INSERT INTO classification_logs (image_id, label, confidence) VALUES (?, ?, ?)',
                    (image_id, classification_label, classification_confidence)
                )
                
                self.log(f"INFO - New image ID {image_id} classified as '{classification_label}' with confidence {classification_confidence}")
            
            self.commit()
            self.close()
            
            return image_id
        except Exception as e:
            self.log(f"ERROR - Failed to upload image: {e}")
            self.close()
            return None
    
    def update_image_classification(self, image_id, label, confidence):
        """Update image with classification results"""
        self.connect()
        
        try:
            # Update the image record with classification
            self.cursor.execute(
                'UPDATE images SET classification_label = ?, classification_confidence = ? WHERE id = ?',
                (label, confidence, image_id)
            )
            
            # Log the classification
            self.cursor.execute(
                'INSERT INTO classification_logs (image_id, label, confidence) VALUES (?, ?, ?)',
                (image_id, label, confidence)
            )
            
            self.log(f"INFO - Image ID {image_id} classified as '{label}' with confidence {confidence}")
            
            self.commit()
            self.close()
            return True
        except Exception as e:
            self.log(f"ERROR - Failed to update image classification: {e}")
            self.close()
            return False
    
    def get_classification_logs(self, image_id=None, limit=50):
        """Get classification logs, optionally filtered by image_id"""
        self.connect()
        
        try:
            if image_id:
                self.cursor.execute(
                    '''SELECT cl.*, i.url, i.caption 
                       FROM classification_logs cl 
                       JOIN images i ON cl.image_id = i.id 
                       WHERE cl.image_id = ? 
                       ORDER BY cl.timestamp DESC LIMIT ?''',
                    (image_id, limit)
                )
            else:
                self.cursor.execute(
                    '''SELECT cl.*, i.url, i.caption 
                       FROM classification_logs cl 
                       JOIN images i ON cl.image_id = i.id 
                       ORDER BY cl.timestamp DESC LIMIT ?''',
                    (limit,)
                )
            
            logs = [dict(row) for row in self.cursor.fetchall()]
            self.close()
            
            return logs
        except Exception as e:
            self.log(f"ERROR - Failed to get classification logs: {e}")
            self.close()
            return []
    
    def get_images_by_classification(self, classification_label, limit=20):
        """Get images filtered by classification label"""
        self.connect()
        
        try:
            self.cursor.execute('''
            SELECT id, url, caption, category, user_id, is_default, created_at, 
                   classification_label, classification_confidence
            FROM images
            WHERE classification_label = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (classification_label, limit))
            
            images = [dict(row) for row in self.cursor.fetchall()]
            self.close()
            
            return images
        except Exception as e:
            self.log(f"ERROR - Failed to get images by classification: {e}")
            self.close()
            return []
    
    def get_comments(self, image_id):
        """Get comments for an image"""
        self.connect()
        
        self.cursor.execute('''
        SELECT c.id, c.image_id, c.user_id, c.text, c.timestamp, u.username
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.image_id = ?
        ORDER BY c.timestamp
        ''', (image_id,))
        
        comments = [dict(row) for row in self.cursor.fetchall()]
        self.close()
        
        return comments
    
    def add_comment(self, image_id, text, user_id=None):
        """Add a comment to an image"""
        self.connect()
        
        self.cursor.execute(
            'INSERT INTO comments (image_id, user_id, text) VALUES (?, ?, ?)',
            (image_id, user_id, text)
        )
        
        self.commit()
        self.close()
        
        return True
    
   
    def get_saved_images(self, user_id):
        """Get saved images for a user"""
        self.connect()
        
        self.cursor.execute('''
        SELECT i.*
        FROM images i
        JOIN saved_images s ON i.id = s.image_id
        WHERE s.user_id = ?
        ORDER BY s.saved_at DESC
        ''', (user_id,))
        
        images = [dict(row) for row in self.cursor.fetchall()]
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
            self.close()
            return True
        except sqlite3.IntegrityError:
            # Image already saved
            self.close()
            return False
    
    def is_image_saved_by_user(self, user_id, image_id):
        """Check if an image is saved by a user"""
        self.connect()
        
        self.cursor.execute(
            'SELECT 1 FROM saved_images WHERE user_id = ? AND image_id = ?',
            (user_id, image_id)
        )
        
        is_saved = self.cursor.fetchone() is not None
        self.close()
        
        return is_saved
        
    def unsave_image_for_user(self, user_id, image_id):
        """Remove an image from a user's saved images"""
        self.connect()
        
        try:
            self.cursor.execute(
                'DELETE FROM saved_images WHERE user_id = ? AND image_id = ?',
                (user_id, image_id)
            )
            
            self.commit()
            self.close()
            return True
        except Exception as e:
            self.log(f"ERROR - Failed to unsave image: {e}")
            self.close()
            return False

    def get_saved_count(self, user_id):
        """Get count of saved images for a user"""
        self.connect()
        
        self.cursor.execute('SELECT COUNT(*) FROM saved_images WHERE user_id = ?', (user_id,))
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count

    def get_uploaded_count(self, user_id):
        """Get count of images uploaded by a user"""
        self.connect()
        
        self.cursor.execute(
            'SELECT COUNT(*) FROM images WHERE user_id = ? AND is_default = 0',
            (user_id,)
        )
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count

    def get_comment_count(self, user_id):
        """Get count of comments posted by a user"""
        self.connect()
        
        self.cursor.execute('SELECT COUNT(*) FROM comments WHERE user_id = ?', (user_id,))
        
        count = self.cursor.fetchone()[0]
        self.close()
        
        return count