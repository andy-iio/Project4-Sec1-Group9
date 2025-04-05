import sqlite3
import base64
import os
import time
from datetime import datetime

class PreppersDB:
    """
    SQLite database for handling the Preppers application dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    """
    
    def __init__(self, db_file='preppers.db'):
        """Initialize the database connection"""
        self.db_file = db_file
        self.create_tables()
        
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  
        return conn
        
    def create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create images table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            caption TEXT,
            tags TEXT,
            user_id INTEGER,
            image_path TEXT,
            upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create saved_images table for users saved images
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_id INTEGER,
            saved_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (image_id) REFERENCES images (id),
            UNIQUE(user_id, image_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    
    def add_user(self, username, password, email=None):
        """Add a new user to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, password, email)
            )
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Username or email already exists"
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return True, user['id']
        else:
            return False, "Invalid username or password"
    
    # Image management methods
    def save_image(self, filename, caption, tags, user_id, image_data=None):
        """Save image metadata and optionally the image file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create images directory if it doesn't exist
        image_dir = 'static/images/uploads'
        os.makedirs(image_dir, exist_ok=True)
        
        # Save the image file if image_data is provided
        image_path = None
        if image_data:
            # Decode base64 string
            image_bytes = base64.b64decode(image_data)
            
            # Create a unique filename based on timestamp
            timestamp = int(time.time())
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{timestamp}{file_extension}"
            
            # Full path to save the image
            image_path = os.path.join(image_dir, unique_filename)
            
            # Save the image file
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
        
        try:
            cursor.execute(
                "INSERT INTO images (filename, caption, tags, user_id, image_path) VALUES (?, ?, ?, ?, ?)",
                (filename, caption, tags, user_id, image_path)
            )
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def get_images(self, limit=20):
        """Get recent images"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT i.id, i.filename, i.caption, i.tags, i.image_path, i.upload_date, u.username 
            FROM images i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.upload_date DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        images = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return images
    
    def get_user_saved_images(self, user_id):
        """Get images saved by a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT i.id, i.filename, i.caption, i.tags, i.image_path, i.upload_date, u.username 
            FROM images i
            JOIN saved_images s ON i.id = s.image_id
            JOIN users u ON i.user_id = u.id
            WHERE s.user_id = ?
            ORDER BY s.saved_date DESC
            """,
            (user_id,)
        )
        
        images = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return images
    
    def save_image_for_user(self, user_id, image_id):
        """Save an image for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO saved_images (user_id, image_id) VALUES (?, ?)",
                (user_id, image_id)
            )
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Image already saved by this user"
        finally:
            conn.close()
    
    def unsave_image_for_user(self, user_id, image_id):
        """Remove an image from a user's saved images"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM saved_images WHERE user_id = ? AND image_id = ?",
            (user_id, image_id)
        )
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0