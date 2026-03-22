from .authentication_page import MainWindow as AuthWindow
from .database import (
    create_db, validate_login, register_user, 
    check_email_verified, update_user_language
)
from .server import app as flask_app