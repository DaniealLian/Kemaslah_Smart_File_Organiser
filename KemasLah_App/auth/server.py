import os
import uuid
import random
import bcrypt
import psycopg2

from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, url_for
from authlib.integrations.flask_client import OAuth

from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, FLASK_SECRET_KEY, FLASK_PORT
from .mailer import send_verification_email, send_otp_email

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def get_db_connection():
    try:
        return psycopg2.connect(
            host="aws-1-ap-northeast-1.pooler.supabase.com",
            database="postgres",
            user="postgres.urzssrfwuyhkebkwcbdx",
            password="nc9@nftkbZ8g-#F",
            sslmode="require"
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None


# -------------------------------
# GOOGLE OAUTH
# -------------------------------
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


# -------------------------------
# BASIC TEST ROUTE
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "API running"}), 200


# -------------------------------
# REGISTER
# -------------------------------
@app.route("/register", methods=["POST"])
def register():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"message": "All fields are required"}), 400

        # Check if email verified first
        cur.execute(
            "SELECT verified FROM email_verifications WHERE email = %s",
            (email,)
        )
        email_row = cur.fetchone()

        if not email_row or email_row[0] is not True:
            return jsonify({"message": "EMAIL_NOT_VERIFIED"}), 400

        # Check email exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"message": "EMAIL_EXISTS"}), 400

        # Check username exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({"message": "USERNAME_EXISTS"}), 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cur.execute(
            """
            INSERT INTO users (username, email, password, auth_provider, email_verified)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (username, email, hashed, "local", True)
        )
        user_id = cur.fetchone()[0]

        # Create profile
        cur.execute(
            """
            INSERT INTO user_profiles (user_id, display_name, language_code)
            VALUES (%s, %s, %s)
            """,
            (user_id, username, "en")
        )

        conn.commit()
        return jsonify({"message": "User registered"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Register failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# LOGIN
# -------------------------------
@app.route("/login", methods=["POST"])
def login():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}

        email = data.get("username", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"message": "All fields are required"}), 400

        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.password, up.display_name, up.language_code
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.email = %s
            """,
            (email,)
        )
        result = cur.fetchone()

        if not result:
            return jsonify({"message": "Invalid credentials"}), 401

        user_id, username, user_email, stored_password, display_name, language_code = result

        if stored_password and bcrypt.checkpw(password.encode(), stored_password.encode()):
            return jsonify({
                "message": "Login success",
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": user_email,
                    "display_name": display_name or username,
                    "language_code": language_code or "en"
                }
            }), 200

        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"message": f"Login failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# REQUEST OTP
# -------------------------------
@app.route("/request-otp", methods=["POST"])
def request_otp():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"message": "Email is required"}), 400

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if not cur.fetchone():
            return jsonify({"message": "Email not registered"}), 404

        otp = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        cur.execute(
            """
            INSERT INTO password_otps (email, otp_code, expires_at, used)
            VALUES (%s, %s, %s, %s)
            """,
            (email, otp, expires_at, False)
        )
        conn.commit()

        send_otp_email(email, otp)

        return jsonify({"message": "OTP sent"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# VERIFY OTP
# -------------------------------
@app.route("/verify-otp", methods=["POST"])
def verify_otp_api():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return jsonify({"message": "Email and OTP are required"}), 400

        cur.execute(
            """
            SELECT id FROM password_otps
            WHERE email = %s AND otp_code = %s AND used = FALSE AND expires_at > NOW()
            ORDER BY id DESC
            LIMIT 1
            """,
            (email, otp)
        )
        row = cur.fetchone()

        if row:
            return jsonify({"message": "OTP valid"}), 200

        return jsonify({"message": "Invalid or expired OTP"}), 400

    except Exception as e:
        return jsonify({"message": f"Failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# RESET PASSWORD
# -------------------------------
@app.route("/reset-password", methods=["POST"])
def reset_password():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        otp = data.get("otp", "").strip()
        new_password = data.get("new_password", "")

        if not email or not otp or not new_password:
            return jsonify({"message": "Email, OTP, and new password are required"}), 400

        cur.execute(
            """
            SELECT id FROM password_otps
            WHERE email = %s AND otp_code = %s AND used = FALSE AND expires_at > NOW()
            ORDER BY id DESC
            LIMIT 1
            """,
            (email, otp)
        )
        otp_row = cur.fetchone()

        if not otp_row:
            return jsonify({"message": "Invalid or expired OTP"}), 400

        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        cur.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
        cur.execute("UPDATE password_otps SET used = TRUE WHERE id = %s", (otp_row[0],))

        conn.commit()
        return jsonify({"message": "Password updated"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Reset failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# REQUEST EMAIL VERIFICATION
# -------------------------------
@app.route("/request-email-verification", methods=["POST"])
def request_email_verification():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"message": "Email is required"}), 400

        send_verification_email(email, email)
        return jsonify({"message": "Verification email sent"}), 200

    except Exception as e:
        return jsonify({"message": f"Failed to send verification email: {str(e)}"}), 500


# -------------------------------
# CHECK EMAIL VERIFIED
# -------------------------------
@app.route("/check-email-verified", methods=["POST"])
def check_email_verified_api():
    conn = get_db_connection()
    if not conn:
        return jsonify({"verified": False, "message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"verified": False}), 400

        cur.execute(
            "SELECT verified FROM email_verifications WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()

        if row and row[0] is True:
            return jsonify({"verified": True}), 200

        return jsonify({"verified": False}), 200

    except Exception as e:
        return jsonify({"verified": False, "message": str(e)}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# VERIFY EMAIL PAGE
# -------------------------------
@app.route("/verify-email")
def verify_email():
    conn = get_db_connection()
    if not conn:
        return "<h1>Database offline</h1>", 500

    cur = conn.cursor()

    try:
        email = request.args.get("email", "").strip().lower()

        if not email:
            return "<h1>Invalid verification link</h1>", 400

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

        return """
        <html>
            <body style="background-color:#0B1426; color:white; font-family:sans-serif; text-align:center; display:flex; justify-content:center; align-items:center; height:100vh;">
                <div style="background-color:#1A202C; padding:40px; border-radius:20px;">
                    <h2 style="color:#48BB78;">Email Verified Successfully ✅</h2>
                    <p>You can now return to the application and register.</p>
                </div>
            </body>
        </html>
        """

    except Exception as e:
        conn.rollback()
        return f"<h1>Verification failed: {str(e)}</h1>", 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# CREATE GOOGLE LOGIN REQUEST
# -------------------------------
@app.route("/create-login-request", methods=["POST"])
def create_login_request_api():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        state_id = str(uuid.uuid4())

        cur.execute(
            """
            INSERT INTO login_requests (state_id, status)
            VALUES (%s, %s)
            """,
            (state_id, "pending")
        )
        conn.commit()

        return jsonify({"state_id": state_id}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# GOOGLE LOGIN START
# -------------------------------
@app.route("/login/google")
def login_google():
    state_id = request.args.get("state_id", "").strip()

    if not state_id:
        return "Missing state_id", 400

    session["state_id"] = state_id
    redirect_uri = url_for("login_google_callback", _external=True)
    return google.authorize_redirect(redirect_uri, prompt="select_account")


# -------------------------------
# GOOGLE LOGIN CALLBACK
# -------------------------------
@app.route("/login/google/callback")
def login_google_callback():
    conn = get_db_connection()
    if not conn:
        return "<h1>Database offline</h1>", 500

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
            return "<h1>Google login failed: missing required data.</h1>", 400

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
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

        return """
        <html>
            <body style="background-color:#0B1426; color:white; font-family:sans-serif; text-align:center; display:flex; justify-content:center; align-items:center; height:100vh;">
                <div style="background-color:#1A202C; padding:40px; border-radius:20px;">
                    <h2 style="color:#48BB78;">Google login successful ✅</h2>
                    <p>You can return to the desktop app now.</p>
                </div>
            </body>
        </html>
        """

    except Exception as e:
        conn.rollback()
        return f"<h1>Google login failed: {str(e)}</h1>", 500

    finally:
        cur.close()
        conn.close()


# -------------------------------
# CHECK GOOGLE LOGIN STATUS
# -------------------------------
@app.route("/check-login-status", methods=["POST"])
def check_login_status_api():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        state_id = data.get("state_id", "").strip()

        if not state_id:
            return jsonify({"message": "State ID required"}), 400

        cur.execute(
            """
            SELECT email, status
            FROM login_requests
            WHERE state_id = %s
            """,
            (state_id,)
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"status": "not_found"}), 404

        email, status = row

        return jsonify({
            "status": status,
            "email": email
        }), 200

    except Exception as e:
        return jsonify({"message": f"Failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()

@app.route("/profile", methods=["GET"])
def get_profile():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        email = request.args.get("email", "").strip().lower()

        if not email:
            return jsonify({"message": "Email is required"}), 400

        cur.execute(
            """
            SELECT u.username, u.email, up.display_name, up.language_code
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.email = %s
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
            "language_code": row[3] or "en"
        }), 200

    except Exception as e:
        return jsonify({"message": f"Failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/profile/update", methods=["POST"])
def update_profile():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        display_name = data.get("display_name", "").strip()
        language_code = data.get("language_code", "en")

        if not email:
            return jsonify({"message": "Email is required"}), 400

        if not display_name:
            return jsonify({"message": "Display name is required"}), 400

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        row = cur.fetchone()

        if not row:
            return jsonify({"message": "User not found"}), 404

        user_id = row[0]

        cur.execute(
            """
            UPDATE user_profiles
            SET display_name = %s, language_code = %s
            WHERE user_id = %s
            """,
            (display_name, language_code, user_id)
        )

        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Update failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/profile/delete", methods=["POST"])
def delete_profile():
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database offline"}), 500

    cur = conn.cursor()

    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"message": "Email is required"}), 400

        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()

        return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Delete failed: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    app.run(port=FLASK_PORT, debug=True)