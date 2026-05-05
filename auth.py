import sqlite3
import hashlib
import os

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 10
        )
    ''')
    conn.commit()
    conn.close()

def _hash_password(password: str) -> str:
    """Hash a password for storing."""
    # Using simple SHA-256 for MVP. In production, use bcrypt or PBKDF2 with salt.
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password, initial_credits=10):
    """Register a new user. Returns (True, "") on success, (False, error_message) on failure."""
    if not username or not password:
        return False, "Username and password cannot be empty."
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists."
        
    pw_hash = _hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password_hash, credits) VALUES (?, ?, ?)", 
                 (username, pw_hash, initial_credits))
        conn.commit()
        success = True
        msg = "Registration successful."
    except Exception as e:
        success = False
        msg = f"Database error: {e}"
    finally:
        conn.close()
        
    return success, msg

def authenticate_user(username, password):
    """Verify username and password. Returns True if valid."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return False
        
    stored_hash = row[0]
    return stored_hash == _hash_password(password)

def get_credits(username):
    """Return the current credits for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return 0

def deduct_credits(username, amount=1):
    """Deduct credits from user. Returns True if successful, False if insufficient credits."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT credits FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    
    if not row or row[0] < amount:
        conn.close()
        return False
        
    new_credits = row[0] - amount
    c.execute("UPDATE users SET credits = ? WHERE username = ?", (new_credits, username))
    conn.commit()
    conn.close()
    return True
