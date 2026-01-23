from flask import Flask, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Helper to connect to your FYP database
def get_db_connection():
    # Relative path to your database file
    conn = sqlite3.connect("kemaslah.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/verify')
def verify():
    # In this new flow, the 'token' sent in the email link is the user's email address
    email = request.args.get('token')
    
    if not email:
        return "<h1>Invalid Request</h1>", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # NEW LOGIC: Insert or Update the VerifiedEmails table
        # This allows the PyQt app to see that this specific email is now cleared for registration
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

    # Define UI style matching your Kemaslah dark theme
    style = """
    <style>
        body { 
            background-color: #0B1426; 
            color: white; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .card { 
            background-color: #1A202C; 
            padding: 50px; 
            border-radius: 25px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            max-width: 450px;
        }
        .icon { font-size: 60px; margin-bottom: 20px; }
        h1 { color: #3182CE; margin-bottom: 10px; font-size: 24px; }
        p { color: #A0AEC0; line-height: 1.6; font-size: 16px; }
        .footer { color: #718096; font-size: 12px; margin-top: 20px; }
    </style>
    """

    if success:
        # Success HTML: User is now allowed to continue registration
        return f"""
        <html>
            <head>{style}</head>
            <body>
                <div class="card">
                    <div class="icon">✅</div>
                    <h1>Email Verified!</h1>
                    <p>Your email <b>{email}</b> has been successfully verified.</p>
                    <p>Please return to the <b>Kemaslah app</b> to complete your account registration.</p>
                    <div class="footer">You can safely close this browser window.</div>
                </div>
            </body>
        </html>
        """
    else:
        # Error HTML
        return f"""
        <html>
            <head>{style}</head>
            <body>
                <div class="card">
                    <div class="icon">❌</div>
                    <h1 style="color: #E53E3E;">Verification Failed</h1>
                    <p>We encountered an error while verifying your email.</p>
                    <p>Please try clicking the "Verify" button in the app again.</p>
                </div>
            </body>
        </html>
        """

if __name__ == '__main__':
    # Flask runs on port 5000 by default
    app.run(port=5000, debug=True)