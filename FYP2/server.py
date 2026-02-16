from flask import Flask, request, url_for, session, redirect
import sqlite3
import os
from datetime import datetime
# Import Authlib for Google Login
from authlib.integrations.flask_client import OAuth
# Import database functions to save the user
from database import register_user, complete_login_request, DB_NAME

app = Flask(__name__)
# IMPORTANT: Change this to a random secret string for security
app.secret_key = "super_secret_key_for_session_security" 

# --- GOOGLE OAUTH CONFIGURATION ---
app.config['GOOGLE_CLIENT_ID'] = '565755337222-4m20r04qohjrsgdd80masi8br9g6m2it.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

oauth = OAuth(app)

# FIXED: Configuration using server metadata
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- EXISTING: EMAIL VERIFICATION ROUTE ---
@app.route('/verify')
def verify():
    email = request.args.get('token')
    if not email: return "<h1>Invalid Request</h1>", 400

    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO VerifiedEmails (email, is_verified, verified_at) 
            VALUES (?, 1, ?)
            ON CONFLICT(email) DO UPDATE SET is_verified=1, verified_at=?
        """, (email, datetime.now(), datetime.now()))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Database error: {e}")
        success = False
    finally:
        conn.close()

    # Reuse your existing style
    style = """
    <style>
        body { background-color: #0B1426; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background-color: #1A202C; padding: 50px; border-radius: 25px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 450px; }
        .icon { font-size: 60px; margin-bottom: 20px; }
        h1 { color: #3182CE; margin-bottom: 10px; }
        p { color: #A0AEC0; }
    </style>
    """

    if success:
        return f"<html><head>{style}</head><body><div class='card'><div class='icon'>✅</div><h1>Email Verified!</h1><p>You can return to the app.</p></div></body></html>"
    else:
        return f"<html><head>{style}</head><body><div class='card'><div class='icon'>❌</div><h1>Failed</h1><p>Verification error.</p></div></body></html>"

# --- NEW: GOOGLE LOGIN ROUTES ---

@app.route('/login/google')
def login_google():
    """
    Step 1: Desktop App sends user here with a 'state_id'.
    We save that ID and send the user to Google.
    """
    state_id = request.args.get('state_id')
    if not state_id:
        return "Missing state_id", 400
    
    # Save the state_id in the browser session so we remember it when they come back
    session['desktop_state_id'] = state_id
    
    # Send user to Google's login page
    redirect_uri = url_for('google_auth', _external=True)
    
    # FIXED: Added prompt='select_account' to force Google to show the account chooser
    return google.authorize_redirect(redirect_uri, prompt='select_account')

@app.route('/callback/google')
def google_auth():
    """
    Step 2: User comes back from Google successfully.
    We get their email and update the database so the Desktop App knows they finished.
    """
    try:
        # Get user info from Google
        token = google.authorize_access_token()
        
        # FIXED: Use the FULL URL to prevent "No scheme supplied" error
        user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
        
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        if not email:
            return "<h1>Login Failed: No email returned from Google.</h1>"

        # 1. Register user if they are new
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE email = ?", (email,))
        if not cursor.fetchone():
            # Auto-register new Google user with a dummy password
            print(f"Registering new Google user: {email}")
            dummy_pass = f"GOOGLE_AUTH_{os.urandom(8).hex()}"
            register_user(name, email, dummy_pass)
        conn.close()
        
        # 2. Notify the Desktop App (Update LoginState table)
        state_id = session.get('desktop_state_id')
        if state_id:
            complete_login_request(state_id, email)
            
        # 3. Show Success Page
        return f"""
        <html>
            <body style="background-color:#0B1426; color:white; font-family:sans-serif; text-align:center; display:flex; justify-content:center; align-items:center; height:100vh;">
                <div style="background-color:#1A202C; padding:40px; border-radius:20px;">
                    <h1 style="color:#48BB78;">Login Successful!</h1>
                    <p style="font-size:18px;">Welcome, {name}</p>
                    <p style="color:#A0AEC0;">You can close this window and return to the app.</p>
                </div>
            </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Login Failed: {e}</h1>"

if __name__ == '__main__':
    # Ensure DB exists before starting
    if not os.path.exists(DB_NAME):
        print("Warning: Database file not found. Run authentication_page.py first to create it.")
        
    app.run(port=5000, debug=True)