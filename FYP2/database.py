import sqlite3
import hashlib
import uuid  # NEW: Required for generating unique login IDs
from datetime import datetime, timedelta

DB_NAME = "kemaslah.db"

def hash_password(password):
    """Encodes the password for security using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_db():
    """Initializes the database and tables based on the Data Dictionary."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create Language table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Language (
            language_id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_name TEXT NOT NULL UNIQUE,
            language_code TEXT UNIQUE
        )
    """)

    # --- FIX: MIGRATION BLOCK (Adds missing column to existing DB) ---
    cursor.execute("PRAGMA table_info(Language)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'language_code' not in columns:
        print("Migrating Database: Adding 'language_code' column to Language table...")
        try:
            cursor.execute("ALTER TABLE Language ADD COLUMN language_code TEXT")
            # Create a unique index to enforce uniqueness on the new column
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_lang_code ON Language(language_code)")
        except sqlite3.Error as e:
            print(f"Migration warning: {e}")
    # ----------------------------------------------------------------

    # 2. NEW: Table to track Google Login state between App and Browser
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LoginState (
            state_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'PENDING', -- PENDING, SUCCESS, FAILED
            user_email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table to track pre-registration email verification status
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS VerifiedEmails (
            email NVARCHAR(100) PRIMARY KEY,
            is_verified BOOLEAN DEFAULT 0,
            verified_at DATETIME
        )
    """)

    # PasswordReset Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PasswordReset (
            reset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email NVARCHAR(100) NOT NULL,
            otp_code NVARCHAR(10) NOT NULL,
            otp_generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            otp_expires_at DATETIME,
            otp_verified BOOLEAN DEFAULT 0,
            reset_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES User(user_id)
        )
    """)

    # User table with preferred_language_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username NVARCHAR(50) NOT NULL UNIQUE,
            email NVARCHAR(100) NOT NULL UNIQUE,
            password_hash NVARCHAR(255) NOT NULL,
            profile_picture NVARCHAR(255),
            initials NVARCHAR(5),
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1,
            preferred_language_id INTEGER DEFAULT 1,
            FOREIGN KEY (preferred_language_id) REFERENCES Language(language_id)
        )
    """)

    # UserProfile Table Integration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserProfile (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            display_name NVARCHAR(100),
            pfp_path NVARCHAR(255),
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES User(user_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Initialize default languages
    init_languages()
    
    print("Database initialized successfully.")

# --- NEW: GOOGLE LOGIN HELPERS ---

def create_login_request():
    """Generates a unique state ID for the login session."""
    state_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO LoginState (state_id) VALUES (?)", (state_id,))
    conn.commit()
    conn.close()
    return state_id

def complete_login_request(state_id, email):
    """Called by Server when Google confirms identity."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE LoginState SET status = 'SUCCESS', user_email = ? WHERE state_id = ?", (email, state_id))
    conn.commit()
    conn.close()

def check_login_status(state_id):
    """Called by App to check if login is done."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status, user_email FROM LoginState WHERE state_id = ?", (state_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == 'SUCCESS':
        return row[1] # Return Email
    return None

# --- LANGUAGE FUNCTIONS ---

def init_languages():
    """Pre-fills the Language table with defaults including translation codes."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Languages with Google Translate language codes
        languages = [
            ("English", "en"),
            ("Bahasa Melayu", "ms"),
            ("Chinese (Simplified)", "zh-CN"),
            ("Tamil", "ta")
        ]
        
        for lang_name, lang_code in languages:
            # 1. Update existing rows (Fixes the NULL issue for old data)
            cursor.execute("UPDATE Language SET language_code = ? WHERE language_name = ?", (lang_code, lang_name))
            # 2. Insert new rows if they don't exist
            cursor.execute(
                "INSERT OR IGNORE INTO Language (language_name, language_code) VALUES (?, ?)", 
                (lang_name, lang_code)
            )
            
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Language init error: {e}")

def get_all_languages():
    """Returns a list of (id, name, code) tuples for all available languages."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT language_id, language_name, language_code FROM Language")
    langs = cursor.fetchall()
    conn.close()
    return langs

def get_language_code(language_id):
    """Gets the language code for a given language_id."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT language_code FROM Language WHERE language_id = ?", (language_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "en"

def update_user_language(email, language_id):
    """Updates the preferred_language_id for a user."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE User SET preferred_language_id = ? WHERE email = ?", (language_id, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

# --- OTP / PASSWORD RESET FUNCTIONS ---

def store_otp(email, otp):
    """Stores a new OTP request using your specific field names."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM User WHERE email = ?", (email,))
    user = cursor.fetchone()
    u_id = user[0] if user else None
    
    expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO PasswordReset (user_id, email, otp_code, otp_expires_at, otp_verified, reset_completed) 
        VALUES (?, ?, ?, ?, 0, 0)
    """, (u_id, email, otp, expires_at))
    
    conn.commit()
    conn.close()

def verify_otp(email, otp):
    """Checks if OTP is correct, not expired, and marks as verified."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        SELECT reset_id FROM PasswordReset 
        WHERE email = ? AND otp_code = ? AND otp_expires_at > ? AND otp_verified = 0
        ORDER BY otp_generated_at DESC LIMIT 1
    """, (email, otp, now))
    
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE PasswordReset SET otp_verified = 1 WHERE reset_id = ?", (result[0],))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def update_password(email, new_password):
    """Updates password and marks the specific reset request as completed."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_val = hash_password(new_password)
    
    cursor.execute("UPDATE User SET password_hash = ? WHERE email = ?", (hashed_val, email))
    
    cursor.execute("""
        UPDATE PasswordReset 
        SET reset_completed = 1 
        WHERE reset_id = (
            SELECT reset_id FROM PasswordReset 
            WHERE email = ? AND otp_verified = 1 
            ORDER BY otp_generated_at DESC LIMIT 1
        )
    """, (email,))
    
    conn.commit()
    conn.close()

# --- REGISTRATION / LOGIN FUNCTIONS ---

def check_email_verified(email):
    """Checks if an email address has completed the pre-registration verification step."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_verified FROM VerifiedEmails WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def register_user(username, email, password):
    """Saves a new user if the username and email are not already taken."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, email FROM User WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        
        if existing:
            if existing[0].lower() == username.lower():
                conn.close(); return "USERNAME_EXISTS"
            if existing[1].lower() == email.lower():
                conn.close(); return "EMAIL_EXISTS"
        
        initials = "".join([n[0].upper() for n in username.split()[:2]])
        
        # Insert with default language ID 1 (English)
        cursor.execute("""
            INSERT INTO User (username, email, password_hash, initials, is_active, preferred_language_id) 
            VALUES (?, ?, ?, ?, ?, 1)
        """, (username, email, hash_password(password), initials, 1))
        
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO UserProfile (user_id, display_name) VALUES (?, ?)", (user_id, username))

        cursor.execute("DELETE FROM VerifiedEmails WHERE email = ?", (email,))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def validate_login(email, password):
    """Checks credentials and returns User data merged with Profile and Language Data."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    hashed = hash_password(password)
    
    # JOIN to get language info
    cursor.execute("""
        SELECT u.*, up.display_name, up.pfp_path, l.language_name, l.language_code
        FROM User u
        LEFT JOIN UserProfile up ON u.user_id = up.user_id
        LEFT JOIN Language l ON u.preferred_language_id = l.language_id
        WHERE u.email = ? AND u.password_hash = ?
    """, (email, hashed))
    
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE User SET last_login = ? WHERE user_id = ?", 
                       (datetime.now(), user['user_id']))
        conn.commit()
    
    conn.close()
    return user

# --- ACCOUNT MANAGEMENT ---

def delete_user_account(email):
    """Permanently deletes a user from User, PasswordReset, and UserProfile tables."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM User WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            user_id = row[0]
            # Delete from UserProfile (New Table)
            cursor.execute("DELETE FROM UserProfile WHERE user_id = ?", (user_id,))
            # Delete from PasswordReset
            cursor.execute("DELETE FROM PasswordReset WHERE user_id = ?", (user_id,))
        
        # Delete from VerifiedEmails and User
        cursor.execute("DELETE FROM VerifiedEmails WHERE email = ?", (email,))
        cursor.execute("DELETE FROM User WHERE email = ?", (email,))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        return False

def update_display_name(email, new_name):
    """Updates the display_name in UserProfile for the given email. Handles missing profiles."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM User WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            user_id = row[0]
            
            cursor.execute("SELECT profile_id FROM UserProfile WHERE user_id = ?", (user_id,))
            profile_exists = cursor.fetchone()
            
            if profile_exists:
                cursor.execute("UPDATE UserProfile SET display_name = ?, updated_at = ? WHERE user_id = ?", 
                               (new_name, datetime.now(), user_id))
            else:
                cursor.execute("INSERT INTO UserProfile (user_id, display_name, updated_at) VALUES (?, ?, ?)", 
                               (user_id, new_name, datetime.now()))
                
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    except sqlite3.Error as e:
        print(f"Update error: {e}")
        return False

if __name__ == "__main__":
    create_db()