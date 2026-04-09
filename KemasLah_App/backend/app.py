import psycopg2
from flask import Flask, request, jsonify
import bcrypt
from datetime import datetime, timedelta
import random
from auth.mailer import send_otp_email
import os
import uuid
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from flask import session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Database connection
conn = psycopg2.connect(
    host="db.urzssrfwuyhkebkwcbdx.supabase.co",
    database="postgres",
    user="postgres",
    password="nc9@nftkbZ8g-#F",
    sslmode="require"
)

@app.route("/")
def home():
    return "API running"

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    cur = conn.cursor()

    try:
        # Check existing email
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            return jsonify({"message": "EMAIL_EXISTS"}), 400

        # Check existing username
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            return jsonify({"message": "USERNAME_EXISTS"}), 400

        # Hash password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert into users table
        cur.execute(
            """
            INSERT INTO users (username, email, password, auth_provider, email_verified)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (username, email, hashed, "local", True)
        )
        user_id = cur.fetchone()[0]

        # Insert default profile
        cur.execute(
            """
            INSERT INTO user_profiles (user_id, display_name, language_code)
            VALUES (%s, %s, %s)
            """,
            (user_id, username, "en")
        )

        conn.commit()
        cur.close()

        return jsonify({"message": "User registered"}), 201

    except Exception as e:
        conn.rollback()
        cur.close()
        return jsonify({"message": f"Register failed: {str(e)}"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.password, up.display_name, up.language_code
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.email=%s
            """,
            (email,)
        )
        result = cur.fetchone()

        if result:
            user_id, username, user_email, stored_password, display_name, language_code = result

            if stored_password and bcrypt.checkpw(password.encode(), stored_password.encode()):
                cur.close()
                return jsonify({
                    "message": "Login success",
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": user_email,
                        "display_name": display_name,
                        "language_code": language_code or "en"
                    }
                }), 200

        cur.close()
        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        cur.close()
        return jsonify({"message": f"Login failed: {str(e)}"}), 500

@app.route("/request-otp", methods=["POST"])
def request_otp():
    data = request.json
    email = data["email"].strip().lower()

    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if not cur.fetchone():
        return jsonify({"message": "Email not registered"}), 404

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    try:
        cur.execute(
            """
            INSERT INTO password_otps (email, otp_code, expires_at, used)
            VALUES (%s, %s, %s, %s)
            """,
            (email, otp, expires_at, False)
        )
        conn.commit()

        send_otp_email(email, otp)

        return jsonify({"message": "OTP sent"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp_api():
    data = request.json
    email = data["email"].strip().lower()
    otp = data["otp"].strip()

    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM password_otps
        WHERE email=%s AND otp_code=%s AND used=FALSE AND expires_at > NOW()
        ORDER BY id DESC
        LIMIT 1
        """,
        (email, otp)
    )
    row = cur.fetchone()

    if row:
        return jsonify({"message": "OTP valid"})
    return jsonify({"message": "Invalid or expired OTP"}), 400

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    email = data["email"].strip().lower()
    otp = data["otp"].strip()
    new_password = data["new_password"]

    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM password_otps
        WHERE email=%s AND otp_code=%s AND used=FALSE AND expires_at > NOW()
        ORDER BY id DESC
        LIMIT 1
        """,
        (email, otp)
    )
    otp_row = cur.fetchone()

    if not otp_row:
        return jsonify({"message": "Invalid or expired OTP"}), 400

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    try:
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))
        cur.execute("UPDATE password_otps SET used=TRUE WHERE id=%s", (otp_row[0],))
        conn.commit()
        return jsonify({"message": "Password updated"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Reset failed: {str(e)}"}), 500

@app.route("/profile", methods=["GET"])
def get_profile():
    email = request.args.get("email", "").strip().lower()

    cur = conn.cursor()
    cur.execute(
        """
        SELECT u.username, u.email, up.display_name, up.pfp_path, up.language_code
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE u.email=%s
        """,
        (email,)
    )
    row = cur.fetchone()

    if not row:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "username": row[0],
        "email": row[1],
        "display_name": row[2],
        "pfp_path": row[3],
        "language_code": row[4]
    })

@app.route("/profile/update", methods=["POST"])
def update_profile():
    data = request.json
    email = data["email"].strip().lower()
    display_name = data["display_name"].strip()
    language_code = data.get("language_code", "en")

    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"message": "User not found"}), 404

        user_id = row[0]
        cur.execute(
            """
            UPDATE user_profiles
            SET display_name=%s, language_code=%s
            WHERE user_id=%s
            """,
            (display_name, language_code, user_id)
        )
        conn.commit()
        return jsonify({"message": "Profile updated"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Update failed: {str(e)}"}), 500

@app.route("/profile/delete", methods=["POST"])
def delete_profile():
    data = request.json
    email = data["email"].strip().lower()

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE email=%s", (email,))
        conn.commit()
        return jsonify({"message": "Account deleted"})
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Delete failed: {str(e)}"}), 500

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

@app.route("/create-login-request", methods=["POST"])
def create_login_request_api():
    state_id = str(uuid.uuid4())
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO login_requests (state_id, status)
            VALUES (%s, %s)
            """,
            (state_id, "pending")
        )
        conn.commit()
        cur.close()
        return jsonify({"state_id": state_id}), 200

    except Exception as e:
        conn.rollback()
        cur.close()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

@app.route("/login/google")
def login_google():
    state_id = request.args.get("state_id", "").strip()

    if not state_id:
        return "Missing state_id", 400

    session["state_id"] = state_id
    redirect_uri = "http://127.0.0.1:5000/login/google/callback"
    return google.authorize_redirect(redirect_uri)

@app.route("/login/google/callback")
def login_google_callback():
    cur = conn.cursor()

    try:
        token = google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            user_info = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()

        email = user_info.get("email", "").strip().lower()
        name = user_info.get("name", "").strip()
        google_sub = user_info.get("sub", "").strip()
        state_id = session.get("state_id")

        if not email or not google_sub or not state_id:
            cur.close()
            return "Google login failed: missing required data.", 400

        # Check if user already exists by email
        cur.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        existing_user = cur.fetchone()

        if existing_user:
            user_id = existing_user[0]

            cur.execute(
                """
                UPDATE users
                SET auth_provider = %s,
                    google_sub = %s,
                    email_verified = TRUE
                WHERE id = %s
                """,
                ("google", google_sub, user_id)
            )

            cur.execute(
                """
                UPDATE user_profiles
                SET display_name = %s
                WHERE user_id = %s
                """,
                (name or email.split("@")[0], user_id)
            )
        else:
            username = email.split("@")[0]

            cur.execute(
                """
                INSERT INTO users (username, email, password, auth_provider, google_sub, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (username, email, None, "google", google_sub, True)
            )
            user_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, language_code)
                VALUES (%s, %s, %s)
                """,
                (user_id, name or username, "en")
            )

        cur.execute(
            """
            UPDATE login_requests
            SET email = %s, status = %s
            WHERE state_id = %s
            """,
            (email, "completed", state_id)
        )

        conn.commit()
        cur.close()

        return """
        <html>
            <body style="font-family: Arial; text-align:center; margin-top:60px;">
                <h2>Google login successful</h2>
                <p>You can return to the desktop app now.</p>
            </body>
        </html>
        """

    except Exception as e:
        conn.rollback()
        cur.close()
        return f"Google login failed: {str(e)}", 500

@app.route("/check-login-status", methods=["POST"])
def check_login_status_api():
    data = request.json
    state_id = data.get("state_id", "").strip()

    if not state_id:
        return jsonify({"message": "State ID required"}), 400

    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT email, status
            FROM login_requests
            WHERE state_id = %s
            """,
            (state_id,)
        )
        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({"status": "not_found"}), 404

        email, status = row

        return jsonify({
            "status": status,
            "email": email
        }), 200

    except Exception as e:
        cur.close()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

@app.route("/mark-email-verified", methods=["POST"])
def mark_email_verified():
    data = request.json
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM email_verifications WHERE email = %s", (email,))
        row = cur.fetchone()

        if row:
            cur.execute(
                "UPDATE email_verifications SET verified = TRUE WHERE email = %s",
                (email,)
            )
        else:
            cur.execute(
                """
                INSERT INTO email_verifications (email, verified)
                VALUES (%s, %s)
                """,
                (email, True)
            )

        conn.commit()
        cur.close()
        return jsonify({"message": "Email verified"}), 200

    except Exception as e:
        conn.rollback()
        cur.close()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

@app.route("/check-email-verified", methods=["POST"])
def check_email_verified_api():
    data = request.json
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"verified": False}), 400

    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT verified FROM email_verifications WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()
        cur.close()

        if row and row[0] is True:
            return jsonify({"verified": True}), 200

        return jsonify({"verified": False}), 200

    except Exception as e:
        cur.close()
        return jsonify({"verified": False, "message": str(e)}), 500

@app.route("/verify-email")
def verify_email():
    email = request.args.get("email", "").strip().lower()

    if not email:
        return "Invalid verification link", 400

    cur = conn.cursor()

    try:
        # Mark email as verified
        cur.execute(
            """
            INSERT INTO email_verifications (email, verified)
            VALUES (%s, %s)
            ON CONFLICT (email)
            DO UPDATE SET verified = TRUE
            """,
            (email, True)
        )

        conn.commit()
        cur.close()

        return """
        <html>
            <body style="font-family: Arial; text-align:center; margin-top:60px;">
                <h2>Email Verified Successfully ✅</h2>
                <p>You can now return to the application and register.</p>
            </body>
        </html>
        """

    except Exception as e:
        conn.rollback()
        cur.close()
        return f"Verification failed: {str(e)}", 500

@app.route("/request-email-verification", methods=["POST"])
def request_email_verification():
    data = request.json
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    try:
        from auth.mailer import send_verification_email

        # Send verification link (you already have /verify-email route)
        send_verification_email(email, email)

        return jsonify({"message": "Verification email sent"}), 200

    except Exception as e:
        return jsonify({"message": f"Failed to send verification email: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)