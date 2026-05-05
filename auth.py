import sqlite3
import hashlib
import os
import secrets

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 10,
            reset_token TEXT
        )
    ''')
    # Migration: add email and reset_token columns if they don't exist (for existing DBs)
    try:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def _hash_password(password: str) -> str:
    """Hash a password for storing."""
    # Using simple SHA-256 for MVP. In production, use bcrypt or PBKDF2 with salt.
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password, email="", initial_credits=10):
    """Register a new user. Returns (True, "") on success, (False, error_message) on failure."""
    if not username or not password:
        return False, "Benutzername und Passwort dürfen nicht leer sein."
    if not email or "@" not in email:
        return False, "Bitte geben Sie eine gültige E-Mail-Adresse ein."
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if username exists
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "Benutzername existiert bereits."
    
    # Check if email exists
    c.execute("SELECT username FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "Diese E-Mail-Adresse ist bereits registriert."
        
    pw_hash = _hash_password(password)
    try:
        c.execute("INSERT INTO users (username, email, password_hash, credits) VALUES (?, ?, ?, ?)", 
                 (username, email, pw_hash, initial_credits))
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

def add_credits(username, amount):
    """Add credits to a user's account. Returns True if user exists."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT credits FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return False
        
    new_credits = row[0] + amount
    c.execute("UPDATE users SET credits = ? WHERE username = ?", (new_credits, username))
    conn.commit()
    conn.close()
    return True

def get_all_users():
    """Return a list of all users with their credit balances and emails."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username, email, credits FROM users ORDER BY username")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_user(username):
    """Delete a user account."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

# --- PASSWORD RESET ---

def generate_reset_token(email):
    """Generate a reset token for a user by email. Returns (token, username) or (None, None)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return None, None
    
    username = row[0]
    token = secrets.token_urlsafe(32)
    c.execute("UPDATE users SET reset_token = ? WHERE username = ?", (token, username))
    conn.commit()
    conn.close()
    return token, username

def reset_password_with_token(token, new_password):
    """Reset password using a token. Returns True if valid token found."""
    if not token or not new_password:
        return False
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE reset_token = ?", (token,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return False
    
    username = row[0]
    new_hash = _hash_password(new_password)
    c.execute("UPDATE users SET password_hash = ?, reset_token = NULL WHERE username = ?", 
              (new_hash, username))
    conn.commit()
    conn.close()
    return True

def get_email_by_username(username):
    """Get email for a username."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
