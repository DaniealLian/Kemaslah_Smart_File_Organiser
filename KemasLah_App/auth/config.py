# auth/config.py
import os

# Email Configuration
SENDER_EMAIL = os.getenv("KEMASLAH_EMAIL", "limzhihao0513@gmail.com")
APP_PASSWORD = os.getenv("KEMASLAH_APP_PASSWORD", "xugmqgryoxqowiez")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "565755337222-4m20r04qohjrsgdd80masi8br9g6m2it.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "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")

# Server
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "super_secret_key_for_session_security")
FLASK_PORT = 5000