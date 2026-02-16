import sys
import os
import re
import threading
import logging
import random
import sqlite3
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QFrame, 
                             QStackedWidget, QMessageBox, QCheckBox, QButtonGroup)
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QUrl # NEW: QUrl
from PyQt6.QtGui import QFont, QIcon, QDesktopServices # NEW: QDesktopServices

# Use deep_translator for Python 3.13 compatibility
from deep_translator import GoogleTranslator

# Import database functions and mailer
# NEW: Added create_login_request and check_login_status to imports
from database import (create_db, register_user, validate_login, 
                      check_email_verified, store_otp, verify_otp, update_password, 
                      delete_user_account, update_display_name,
                      get_all_languages, update_user_language, get_language_code,
                      create_login_request, check_login_status)
from mailer import send_verification_email, send_otp_email
from server import app as flask_app

# --- Translation Cache ---
translation_cache = {}

def translate_text(text, target_lang="en"):
    """
    Translates text to target language using Google Translate.
    """
    if not text or target_lang == "en":
        return text
    
    cache_key = f"{text}_{target_lang}"
    if cache_key in translation_cache:
        return translation_cache[cache_key]
    
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        translation_cache[cache_key] = translated
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# --- WORKER THREAD FOR EMAIL ---
class EmailWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, email, otp):
        super().__init__()
        self.email = email
        self.otp = otp

    def run(self):
        try:
            store_otp(self.email, self.otp)
            send_otp_email(self.email, self.otp)
            self.finished.emit(True, "OTP sent! Please check your inbox.")
        except Exception as e:
            self.finished.emit(False, str(e))

class VerificationWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        try:
            send_verification_email(self.email, self.email)
            self.finished.emit(True, f"Verification link sent to {self.email}. Please check your inbox (and spam).")
        except Exception as e:
            self.finished.emit(False, str(e))

# --- Global Styles ---
INPUT_STYLE = """
    QLineEdit {
        background: transparent !important;
        border: none;
        color: white;
        padding: 8px 2px;
        font-size: 14px;
    }
    QLineEdit:read-only { color: #A0AEC0; }
"""
FIELD_CONTAINER_STYLE = "QWidget { border-bottom: 2px solid #2D3748; background: transparent; }"
CARD_STYLE = "QFrame { background-color: #0B1426; border-radius: 25px; }"
SIDEBAR_BTN_STYLE = """
    QPushButton {
        background-color: transparent; color: #CBD5E0;
        border: none; border-radius: 5px;
        padding: 12px; text-align: left; font-size: 14px;
    }
    QPushButton:hover { background-color: #2D3748; }
"""
TOGGLE_BTN_STYLE = "QPushButton { background: transparent; border: none; padding: 0px; }"
CHECKBOX_STYLE = """
    QCheckBox { color: #CBD5E0; font-size: 14px; padding: 10px; spacing: 10px; }
    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #4A5568; background: transparent; }
    QCheckBox::indicator:checked { background-color: #3182CE; border: 2px solid #3182CE; image: url(assets/check.png); }
    QCheckBox:hover { background-color: #2D3748; border-radius: 5px; }
"""

# --- Validation Helpers ---
def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def is_strong_password(password):
    return re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$', password) is not None

# --- LOGIN PAGE ---
class LoginPage(QWidget):
    def __init__(self, parent_stack, profile_page, language_page):
        super().__init__()
        self.stack = parent_stack
        self.profile_page = profile_page 
        self.language_page = language_page
        self.current_lang = "en"
        
        # --- NEW: Google Login Timer ---
        self.poll_timer = QTimer()
        self.poll_timer.interval = 1000 # Check every 1 second
        self.poll_timer.timeout.connect(self.check_google_status)
        self.current_state_id = None
        
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.basedir = os.path.dirname(__file__)
        self.icon_visible = os.path.join(self.basedir, "assets", "visible.png")
        self.icon_hide = os.path.join(self.basedir, "assets", "hide.png")
        google_icon_path = os.path.join(self.basedir, "assets", "google_icon.png")

        card = QFrame(); card.setFixedSize(400, 650); card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(45, 40, 45, 40)
        
        self.title_label = QLabel("Welcome to Kemaslah")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        
        self.subtitle_label = QLabel("Your smarter file manager")
        self.subtitle_label.setStyleSheet("color: #718096; font-size: 11px;")
        
        e_cont = QWidget(); e_cont.setStyleSheet(FIELD_CONTAINER_STYLE); e_lay = QHBoxLayout(e_cont); e_lay.setContentsMargins(0,0,0,0)
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("Email"); self.email_input.setStyleSheet(INPUT_STYLE); e_lay.addWidget(self.email_input)

        p_cont = QWidget(); p_cont.setStyleSheet(FIELD_CONTAINER_STYLE); p_lay = QHBoxLayout(p_cont); p_lay.setContentsMargins(0,0,0,0)
        self.pass_input = QLineEdit(); self.pass_input.setPlaceholderText("Password"); self.pass_input.setEchoMode(QLineEdit.EchoMode.Password); self.pass_input.setStyleSheet(INPUT_STYLE)
        self.toggle_btn = QPushButton(); self.toggle_btn.setFixedSize(30, 30); self.toggle_btn.setStyleSheet(TOGGLE_BTN_STYLE); self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_eye_icon(self.toggle_btn, True); self.toggle_btn.clicked.connect(lambda: self.toggle_password(self.pass_input, self.toggle_btn))
        p_lay.addWidget(self.pass_input); p_lay.addWidget(self.toggle_btn)

        self.forgot_btn = QPushButton("Forgot Password?")
        self.forgot_btn.setStyleSheet("color: #718096; border: none; text-align: left; font-size: 11px; background: transparent; margin-top: 5px;")
        self.forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(45); self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("QPushButton { background-color: #0D3B66; color: white; border-radius: 22px; font-weight: bold; margin-top: 20px; }")
        self.login_btn.clicked.connect(self.handle_login)

        self.google_btn = QPushButton(" Continue with Google")
        self.google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if os.path.exists(google_icon_path):
            self.google_btn.setIcon(QIcon(google_icon_path)); self.google_btn.setIconSize(QSize(18, 18))
        self.google_btn.setFixedHeight(45)
        self.google_btn.setStyleSheet("QPushButton { background-color: white; color: #2D3748; border-radius: 22px; font-weight: bold; margin-top: 10px; }")
        # --- NEW: Connect Google Button ---
        self.google_btn.clicked.connect(self.handle_google_login)

        self.go_reg = QPushButton("Don't have an account? Register here")
        self.go_reg.setStyleSheet("color: #3182CE; border: none; font-size: 11px; background: transparent;")
        self.go_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go_reg.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(20)
        card_layout.addWidget(e_cont); card_layout.addWidget(p_cont); card_layout.addWidget(self.forgot_btn)
        card_layout.addStretch(); card_layout.addWidget(self.login_btn); card_layout.addWidget(self.google_btn)
        card_layout.addWidget(self.go_reg)
        layout.addWidget(card)

    def update_translations(self, lang_code):
        self.current_lang = lang_code
        self.title_label.setText(translate_text("Welcome to Kemaslah", lang_code))
        self.subtitle_label.setText(translate_text("Your smarter file manager", lang_code))
        self.email_input.setPlaceholderText(translate_text("Email", lang_code))
        self.pass_input.setPlaceholderText(translate_text("Password", lang_code))
        self.forgot_btn.setText(translate_text("Forgot Password?", lang_code))
        self.login_btn.setText(translate_text("Login", lang_code))
        self.google_btn.setText(translate_text(" Continue with Google", lang_code))
        self.go_reg.setText(translate_text("Don't have an account? Register here", lang_code))

    def toggle_password(self, line_edit, btn):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password: line_edit.setEchoMode(QLineEdit.EchoMode.Normal); self.update_eye_icon(btn, False)
        else: line_edit.setEchoMode(QLineEdit.EchoMode.Password); self.update_eye_icon(btn, True)

    def update_eye_icon(self, btn, is_hidden):
        icon_path = self.icon_hide if is_hidden else self.icon_visible
        if os.path.exists(icon_path): btn.setIcon(QIcon(icon_path)); btn.setIconSize(QSize(20, 20))

    def clear_fields(self):
        self.email_input.setText("")
        self.pass_input.setText("")

    # --- NEW: GOOGLE LOGIN LOGIC ---
    
    def handle_google_login(self):
        """Step 1: Open Browser and start polling DB"""
        self.current_state_id = create_login_request()
        
        # Open the Flask server route
        url = f"http://127.0.0.1:5000/login/google?state_id={self.current_state_id}"
        QDesktopServices.openUrl(QUrl(url))
        
        # UI Feedback
        self.google_btn.setEnabled(False)
        self.google_btn.setText("Waiting for browser...")
        
        # Start checking DB every 1 second
        self.poll_timer.start()

    def check_google_status(self):
        """Step 2: Check if browser login finished"""
        if not self.current_state_id: return
        
        # Ask DB: "Did user finish?"
        user_email = check_login_status(self.current_state_id)
        
        if user_email:
            # Login Success!
            self.poll_timer.stop()
            self.google_btn.setEnabled(True)
            self.google_btn.setText(" Continue with Google")
            
            # Fetch user data manually (since we don't have the password for validate_login)
            user_data = self.fetch_google_user_data(user_email)
            
            if user_data:
                lang_code = user_data['language_code']
                self.parent().parent().update_all_pages(lang_code)
                self.profile_page.update_profile_info(user_data)
                self.language_page.set_user_data(user_data)
                self.stack.setCurrentIndex(3) # Go to Profile
            else:
                QMessageBox.critical(self, "Error", "Failed to retrieve user data.")

    def fetch_google_user_data(self, email):
        """Helper to get user data without password (trusted from Google)"""
        conn = sqlite3.connect("kemaslah.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*, up.display_name, up.pfp_path, l.language_name, l.language_code
            FROM User u
            LEFT JOIN UserProfile up ON u.user_id = up.user_id
            LEFT JOIN Language l ON u.preferred_language_id = l.language_id
            WHERE u.email = ?
        """, (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    # -------------------------------

    def handle_login(self):
        e, p = self.email_input.text().strip(), self.pass_input.text()
        if not e or not p: 
            QMessageBox.warning(self, "Validation Error", "All fields are required."); return
        user_data = validate_login(e, p)
        if user_data: 
            lang_code = user_data['language_code']
            self.parent().parent().update_all_pages(lang_code) 
            self.profile_page.update_profile_info(user_data)
            self.language_page.set_user_data(user_data)
            self.stack.setCurrentIndex(3)
        else: 
            QMessageBox.critical(self, "Login Failed", "Invalid Email or Password.")

# --- FORGOT PASSWORD PAGE ---
class ForgotPasswordPage(QWidget):
    def __init__(self, parent_stack):
        super().__init__()
        self.stack = parent_stack
        self.countdown = 60 
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card = QFrame(); card.setFixedSize(400, 550); card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(45, 40, 45, 40)

        self.title_label = QLabel("Welcome to Kemaslah")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)); self.title_label.setStyleSheet("color: white;")
        self.subtitle_label = QLabel("To reset your password\nplease enter the OTP sent via your registered email")
        self.subtitle_label.setStyleSheet("color: #CBD5E0; font-size: 11px;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        e_cont = QWidget(); e_cont.setStyleSheet(FIELD_CONTAINER_STYLE); e_lay = QHBoxLayout(e_cont); e_lay.setContentsMargins(0,0,0,0)
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("Email"); self.email_input.setStyleSheet(INPUT_STYLE); e_lay.addWidget(self.email_input)

        o_cont = QWidget(); o_cont.setStyleSheet(FIELD_CONTAINER_STYLE); o_lay = QHBoxLayout(o_cont); o_lay.setContentsMargins(0,0,0,0)
        self.otp_input = QLineEdit(); self.otp_input.setPlaceholderText("OTP"); self.otp_input.setStyleSheet(INPUT_STYLE); o_lay.addWidget(self.otp_input)

        self.req_btn = QPushButton("Request OTP"); self.req_btn.setFixedHeight(40); self.req_btn.setStyleSheet("QPushButton { background-color: #0D3B66; color: white; border-radius: 10px; font-weight: bold; }")
        self.req_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.req_btn.clicked.connect(self.handle_otp_request)

        self.sub_btn = QPushButton("Submit"); self.sub_btn.setFixedHeight(40); self.sub_btn.setStyleSheet("QPushButton { background-color: #0F8E52; color: white; border-radius: 10px; font-weight: bold; }")
        self.sub_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.sub_btn.clicked.connect(self.handle_otp_submit)

        self.back_btn = QPushButton("Back to Login"); self.back_btn.setStyleSheet("color: #718096; border: none; font-size: 11px; background: transparent; margin-top: 10px;")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.resend_timer = QTimer(); self.resend_timer.timeout.connect(self.update_timer_text)

        card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(20)
        card_layout.addWidget(e_cont); card_layout.addWidget(o_cont); card_layout.addSpacing(20)
        card_layout.addWidget(self.req_btn); card_layout.addWidget(self.sub_btn); card_layout.addWidget(self.back_btn); card_layout.addStretch()
        layout.addWidget(card)

    def update_translations(self, lang_code):
        self.title_label.setText(translate_text("Welcome to Kemaslah", lang_code))
        self.subtitle_label.setText(translate_text("To reset your password\nplease enter the OTP sent via your registered email", lang_code))
        self.req_btn.setText(translate_text("Request OTP", lang_code))
        self.sub_btn.setText(translate_text("Submit", lang_code))
        self.back_btn.setText(translate_text("Back to Login", lang_code))
        self.email_input.setPlaceholderText(translate_text("Email", lang_code))
        self.otp_input.setPlaceholderText(translate_text("OTP", lang_code))

    def handle_otp_request(self):
        email = self.email_input.text().strip()
        if not email: QMessageBox.warning(self, "Validation Error", "Email is required."); return
        if not is_valid_email(email): QMessageBox.warning(self, "Format Error", "Invalid email format."); return
        
        conn = sqlite3.connect("kemaslah.db"); cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM User WHERE email = ?", (email,))
        if not cursor.fetchone(): 
            QMessageBox.critical(self, "Error", "This email is not registered.")
            conn.close(); return
        conn.close()

        self.req_btn.setText("Sending...")
        self.req_btn.setEnabled(False)
        otp = str(random.randint(100000, 999999))

        self.worker = EmailWorker(email, otp)
        self.worker.finished.connect(self.on_email_sent)
        self.worker.start()

    def on_email_sent(self, success, message):
        if success:
            QMessageBox.information(self, "Success", message)
            self.countdown = 60
            self.resend_timer.start(1000)
        else:
            QMessageBox.critical(self, "Error", f"Failed to send email: {message}")
            self.req_btn.setText("Request OTP")
            self.req_btn.setEnabled(True)

    def update_timer_text(self):
        if self.countdown > 0: self.req_btn.setText(f"Resend in {self.countdown}s"); self.countdown -= 1
        else: self.resend_timer.stop(); self.req_btn.setEnabled(True); self.req_btn.setText("Resend OTP")

    def handle_otp_submit(self):
        email, otp = self.email_input.text().strip(), self.otp_input.text().strip()
        if not email or not otp: QMessageBox.warning(self, "Validation Error", "All fields are required."); return
        
        try:
            if verify_otp(email, otp): 
                self.stack.widget(4).set_email(email); 
                self.stack.setCurrentIndex(4) 
            else: 
                QMessageBox.critical(self, "Error", "Invalid or expired OTP code.")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"Database error: {e}")

# --- RESET PASSWORD PAGE ---
class ResetPasswordPage(QWidget):
    def __init__(self, parent_stack):
        super().__init__()
        self.stack = parent_stack; self.email = ""
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.basedir = os.path.dirname(__file__)
        self.icon_visible = os.path.join(self.basedir, "assets", "visible.png")
        self.icon_hide = os.path.join(self.basedir, "assets", "hide.png")

        card = QFrame(); card.setFixedSize(400, 550); card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(45, 40, 45, 40)
        
        self.title_label = QLabel("Welcome to Kemaslah")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)); self.title_label.setStyleSheet("color: white;")
        
        self.subtitle_label = QLabel("Enter your new password")
        self.subtitle_label.setStyleSheet("color: #CBD5E0; font-size: 11px;")

        p_cont = QWidget(); p_cont.setStyleSheet(FIELD_CONTAINER_STYLE); p_lay = QHBoxLayout(p_cont); p_lay.setContentsMargins(0,0,0,0)
        self.p_in = QLineEdit(); self.p_in.setPlaceholderText("New Password"); self.p_in.setEchoMode(QLineEdit.EchoMode.Password); self.p_in.setStyleSheet(INPUT_STYLE)
        self.p_t = QPushButton(); self.p_t.setFixedSize(30, 30); self.p_t.setStyleSheet(TOGGLE_BTN_STYLE); self.p_t.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_eye_icon(self.p_t, True); self.p_t.clicked.connect(lambda: self.toggle_password(self.p_in, self.p_t))
        p_lay.addWidget(self.p_in); p_lay.addWidget(self.p_t)

        rp_cont = QWidget(); rp_cont.setStyleSheet(FIELD_CONTAINER_STYLE); rp_lay = QHBoxLayout(rp_cont); rp_lay.setContentsMargins(0,0,0,0)
        self.rp_in = QLineEdit(); self.rp_in.setPlaceholderText("Re-enter New Password"); self.rp_in.setEchoMode(QLineEdit.EchoMode.Password); self.rp_in.setStyleSheet(INPUT_STYLE)
        self.rp_t = QPushButton(); self.rp_t.setFixedSize(30, 30); self.rp_t.setStyleSheet(TOGGLE_BTN_STYLE); self.rp_t.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_eye_icon(self.rp_t, True); self.rp_t.clicked.connect(lambda: self.toggle_password(self.rp_in, self.rp_t))
        rp_lay.addWidget(self.rp_in); rp_lay.addWidget(self.rp_t)

        self.reg_btn = QPushButton("Register"); self.reg_btn.setFixedHeight(40); self.reg_btn.setStyleSheet("QPushButton { background-color: #0D3B66; color: white; border-radius: 10px; font-weight: bold; }")
        self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.reg_btn.clicked.connect(self.handle_final_reset)

        self.back_btn = QPushButton("Back to Login"); self.back_btn.setStyleSheet("color: #718096; border: none; font-size: 11px; background: transparent; margin-top: 10px;")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter); card_layout.addSpacing(20)
        card_layout.addWidget(p_cont); card_layout.addWidget(rp_cont); card_layout.addStretch()
        card_layout.addWidget(self.reg_btn); card_layout.addWidget(self.back_btn)
        layout.addWidget(card)

    def update_translations(self, lang_code):
        self.title_label.setText(translate_text("Welcome to Kemaslah", lang_code))
        self.subtitle_label.setText(translate_text("Enter your new password", lang_code))
        self.p_in.setPlaceholderText(translate_text("New Password", lang_code))
        self.rp_in.setPlaceholderText(translate_text("Re-enter New Password", lang_code))
        self.reg_btn.setText(translate_text("Register", lang_code))
        self.back_btn.setText(translate_text("Back to Login", lang_code))

    def toggle_password(self, line_edit, btn):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password: line_edit.setEchoMode(QLineEdit.EchoMode.Normal); self.update_eye_icon(btn, False)
        else: line_edit.setEchoMode(QLineEdit.EchoMode.Password); self.update_eye_icon(btn, True)

    def update_eye_icon(self, btn, is_hidden):
        icon_path = self.icon_hide if is_hidden else self.icon_visible
        if os.path.exists(icon_path): btn.setIcon(QIcon(icon_path)); btn.setIconSize(QSize(20, 20))

    def set_email(self, email): self.email = email

    def handle_final_reset(self):
        p, rp = self.p_in.text(), self.rp_in.text()
        if not p or not rp: QMessageBox.warning(self, "Validation Error", "All fields are required."); return
        if p != rp: QMessageBox.critical(self, "Error", "Passwords do not match!"); return
        if not is_strong_password(p): QMessageBox.critical(self, "Security Error", "Password must be 10+ chars with Mixed Case and Digit."); return
        update_password(self.email, p); QMessageBox.information(self, "Success", "Password updated!"); self.stack.setCurrentIndex(0)

# --- REGISTER PAGE ---
class RegisterPage(QWidget):
    def __init__(self, parent_stack):
        super().__init__()
        self.stack = parent_stack
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.basedir = os.path.dirname(__file__)
        self.icon_visible = os.path.join(self.basedir, "assets", "visible.png")
        self.icon_hide = os.path.join(self.basedir, "assets", "hide.png")

        card = QFrame(); card.setFixedSize(450, 650); card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(45, 40, 45, 40)
        self.title_label = QLabel("Create Account"); self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)); self.title_label.setStyleSheet("color: white;")

        u_cont = QWidget(); u_cont.setStyleSheet(FIELD_CONTAINER_STYLE); u_lay = QHBoxLayout(u_cont); u_lay.setContentsMargins(0,0,0,0)
        self.u_in = QLineEdit(); self.u_in.setPlaceholderText("Username"); self.u_in.setStyleSheet(INPUT_STYLE); u_lay.addWidget(self.u_in)

        e_cont = QWidget(); e_cont.setStyleSheet(FIELD_CONTAINER_STYLE); e_lay = QHBoxLayout(e_cont); e_lay.setContentsMargins(0,0,0,0)
        self.e_in = QLineEdit(); self.e_in.setPlaceholderText("Email"); self.e_in.setStyleSheet(INPUT_STYLE)
        self.v_btn = QPushButton("Verify"); self.v_btn.setFixedSize(70, 30); self.v_btn.setStyleSheet("background-color: #3182CE; color: white; border-radius: 5px;")
        self.v_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.v_btn.clicked.connect(self.handle_email_verification)
        e_lay.addWidget(self.e_in); e_lay.addWidget(self.v_btn)

        p_cont = QWidget(); p_cont.setStyleSheet(FIELD_CONTAINER_STYLE); p_lay = QHBoxLayout(p_cont); p_lay.setContentsMargins(0,0,0,0)
        self.p_in = QLineEdit(); self.p_in.setPlaceholderText("Password"); self.p_in.setEchoMode(QLineEdit.EchoMode.Password); self.p_in.setStyleSheet(INPUT_STYLE)
        self.p_t = QPushButton(); self.p_t.setFixedSize(30, 30); self.p_t.setStyleSheet(TOGGLE_BTN_STYLE); self.p_t.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_eye_icon(self.p_t, True); self.p_t.clicked.connect(lambda: self.toggle_password(self.p_in, self.p_t))
        p_lay.addWidget(self.p_in); p_lay.addWidget(self.p_t)

        rp_cont = QWidget(); rp_cont.setStyleSheet(FIELD_CONTAINER_STYLE); rp_lay = QHBoxLayout(rp_cont); rp_lay.setContentsMargins(0,0,0,0)
        self.rp_in = QLineEdit(); self.rp_in.setPlaceholderText("Re-enter Password"); self.rp_in.setEchoMode(QLineEdit.EchoMode.Password); self.rp_in.setStyleSheet(INPUT_STYLE)
        self.rp_t = QPushButton(); self.rp_t.setFixedSize(30, 30); self.rp_t.setStyleSheet(TOGGLE_BTN_STYLE); self.rp_t.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_eye_icon(self.rp_t, True); self.rp_t.clicked.connect(lambda: self.toggle_password(self.rp_in, self.rp_t))
        rp_lay.addWidget(self.rp_in); rp_lay.addWidget(self.rp_t)

        self.reg_btn = QPushButton("Register"); self.reg_btn.setEnabled(False); self.reg_btn.setFixedHeight(45); self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_btn.setStyleSheet("QPushButton:enabled { background-color: #0D3B66; color: white; border-radius: 22px; } QPushButton:disabled { background-color: #2D3748; color: #718096; border-radius: 22px; }")
        self.reg_btn.clicked.connect(self.handle_registration)

        self.back_btn = QPushButton("Already have an account? Login"); self.back_btn.setStyleSheet("color: #718096; border: none; font-size: 11px; background: transparent;")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.check_timer = QTimer(); self.check_timer.timeout.connect(self.poll_verification)
        card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter); card_layout.addWidget(u_cont); card_layout.addWidget(e_cont)
        card_layout.addWidget(p_cont); card_layout.addWidget(rp_cont); card_layout.addStretch()
        card_layout.addWidget(self.reg_btn); card_layout.addWidget(self.back_btn); layout.addWidget(card)

    def update_translations(self, lang_code):
        self.title_label.setText(translate_text("Create Account", lang_code))
        self.u_in.setPlaceholderText(translate_text("Username", lang_code))
        self.e_in.setPlaceholderText(translate_text("Email", lang_code))
        self.v_btn.setText(translate_text("Verify", lang_code))
        self.p_in.setPlaceholderText(translate_text("Password", lang_code))
        self.rp_in.setPlaceholderText(translate_text("Re-enter Password", lang_code))
        self.reg_btn.setText(translate_text("Register", lang_code))
        self.back_btn.setText(translate_text("Already have an account? Login", lang_code))

    def toggle_password(self, line_edit, btn):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password: line_edit.setEchoMode(QLineEdit.EchoMode.Normal); self.update_eye_icon(btn, False)
        else: line_edit.setEchoMode(QLineEdit.EchoMode.Password); self.update_eye_icon(btn, True)

    def update_eye_icon(self, btn, is_hidden):
        icon_path = self.icon_hide if is_hidden else self.icon_visible
        if os.path.exists(icon_path): btn.setIcon(QIcon(icon_path)); btn.setIconSize(QSize(20, 20))

    def handle_email_verification(self):
        email = self.e_in.text().strip()
        if not email: QMessageBox.warning(self, "Validation Error", "Please enter an email address."); return
        if not is_valid_email(email): QMessageBox.warning(self, "Format Error", "Invalid email format."); return
        
        self.v_btn.setText("Sending...")
        self.v_btn.setEnabled(False)

        self.worker = VerificationWorker(email)
        self.worker.finished.connect(self.on_verification_sent)
        self.worker.start()

    def on_verification_sent(self, success, message):
        if success:
            QMessageBox.information(self, "Sent", message)
            self.v_btn.setText("Sent")
            self.check_timer.start(3000)
        else:
            QMessageBox.critical(self, "Error", f"Failed: {message}")
            self.v_btn.setText("Verify")
            self.v_btn.setEnabled(True)

    def poll_verification(self):
        email = self.e_in.text().strip()
        if check_email_verified(email): 
            self.check_timer.stop()
            self.reg_btn.setEnabled(True)
            self.v_btn.setText("Verified")
            QMessageBox.information(self, "Verified", "Email verified successfully! You can now click Register.")

    def handle_registration(self):
        u, e, p, rp = self.u_in.text().strip(), self.e_in.text().strip(), self.p_in.text(), self.rp_in.text()
        
        if not all([u, e, p, rp]): QMessageBox.critical(self, "Validation Error", "All fields are required."); return
        if p != rp: QMessageBox.critical(self, "Match Error", "Passwords do not match!"); return
        if not is_strong_password(p): QMessageBox.critical(self, "Security Error", "Password must be 10+ chars with Mixed Case and Digit."); return
        
        if not check_email_verified(e):
             QMessageBox.critical(self, "Error", "Email not verified yet. Please click verify and check your email."); return

        result = register_user(u, e, p)
        if result == True: QMessageBox.information(self, "Success", "Account created successfully!"); self.stack.setCurrentIndex(0)
        elif result == "USERNAME_EXISTS": QMessageBox.warning(self, "Registration Failed", "This username is already taken.")
        elif result == "EMAIL_EXISTS": QMessageBox.warning(self, "Registration Failed", "This email is already registered.")

# --- LANGUAGE PAGE ---
class LanguagePage(QWidget):
    def __init__(self, parent_stack, login_page):
        super().__init__()
        self.stack = parent_stack
        self.login_page = login_page
        self.basedir = os.path.dirname(__file__)
        self.user_email = ""
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(50, 50, 50, 50); main_layout.setSpacing(0)
        
        sidebar = QFrame(); sidebar.setFixedWidth(200); sidebar.setStyleSheet("background-color: #0B1426; border-top-left-radius: 25px; border-bottom-left-radius: 25px;")
        side_lay = QVBoxLayout(sidebar); side_lay.setContentsMargins(10, 30, 10, 30)
        
        self.btn_prof = QPushButton("  User Profile"); self.btn_prof.setStyleSheet(SIDEBAR_BTN_STYLE); self.btn_prof.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prof.clicked.connect(lambda: self.stack.setCurrentIndex(3)); side_lay.addWidget(self.btn_prof)
        
        self.btn_lang = QPushButton("  Language"); self.btn_lang.setStyleSheet(SIDEBAR_BTN_STYLE + "background-color: #2D3748;"); self.btn_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        side_lay.addWidget(self.btn_lang)
        
        self.btn_news = QPushButton("  What's new"); self.btn_news.setStyleSheet(SIDEBAR_BTN_STYLE); side_lay.addWidget(self.btn_news)
        
        side_lay.addStretch()
        self.logout_btn = QPushButton("  Log Out"); self.logout_btn.setFixedHeight(40); self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setStyleSheet("background-color: #FF0000; color: white; border-radius: 10px; font-weight: bold;")
        logout_icon = os.path.join(self.basedir, "assets", "logout.png")
        if os.path.exists(logout_icon): self.logout_btn.setIcon(QIcon(logout_icon))
        self.logout_btn.clicked.connect(self.handle_logout)
        side_lay.addWidget(self.logout_btn)
        
        content = QFrame(); content.setStyleSheet("background-color: #1A202C; border-top-right-radius: 25px; border-bottom-right-radius: 25px;")
        c_lay = QVBoxLayout(content); c_lay.setContentsMargins(40, 30, 40, 40)
        
        header = QHBoxLayout()
        self.title_label = QLabel("Language"); self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); self.title_label.setStyleSheet("color: white; border-bottom: 2px solid white;")
        close_btn = QPushButton("✖"); close_btn.setFixedSize(25, 25); close_btn.setStyleSheet("color: white; background-color: #FF0000; border-radius: 12px;"); close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.title_label); header.addStretch(); header.addWidget(close_btn)
        
        self.subtitle_label = QLabel("Select a Language"); self.subtitle_label.setStyleSheet("color: #718096; font-size: 13px; margin-top: 5px;")
        c_lay.addLayout(header); c_lay.addWidget(self.subtitle_label); c_lay.addSpacing(15)
        
        self.lang_group = QButtonGroup(self)
        self.lang_group.setExclusive(True)
        self.checkboxes = {}
        
        langs = get_all_languages()
        
        for lang_id, lang_name, lang_code in langs:
            cb = QCheckBox(lang_name)
            cb.setStyleSheet(CHECKBOX_STYLE)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            self.lang_group.addButton(cb, lang_id)
            self.checkboxes[lang_id] = (cb, lang_code)
            c_lay.addWidget(cb)
            cb.clicked.connect(lambda _, lid=lang_id, lcode=lang_code: self.save_and_translate(lid, lcode))

        c_lay.addStretch()
        main_layout.addWidget(sidebar); main_layout.addWidget(content)

    def update_translations(self, lang_code):
        self.btn_prof.setText(translate_text("  User Profile", lang_code))
        self.btn_lang.setText(translate_text("  Language", lang_code))
        self.btn_news.setText(translate_text("  What's new", lang_code))
        self.logout_btn.setText(translate_text("  Log Out", lang_code))
        self.title_label.setText(translate_text("Language", lang_code))
        self.subtitle_label.setText(translate_text("Select a Language", lang_code))

    def set_user_data(self, user_data):
        self.user_email = user_data['email']
        current_lang_id = user_data['preferred_language_id']
        if current_lang_id in self.checkboxes:
            self.checkboxes[current_lang_id][0].setChecked(True)

    def save_and_translate(self, lang_id, lang_code):
        if update_user_language(self.user_email, lang_id):
            self.parent().parent().update_all_pages(lang_code)
            QMessageBox.information(self, "Success", f"Language changed to {lang_code.upper()}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save language setting.")
            
    def handle_logout(self):
        self.stack.widget(0).clear_fields()
        self.stack.setCurrentIndex(0)

# --- USER PROFILE PAGE ---
class UserProfilePage(QWidget):
    def __init__(self, parent_stack):
        super().__init__()
        self.stack = parent_stack; self.basedir = os.path.dirname(__file__)
        self.user_email = "" 
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(50, 50, 50, 50); main_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setFixedWidth(200); sidebar.setStyleSheet("background-color: #0B1426; border-top-left-radius: 25px; border-bottom-left-radius: 25px;")
        side_lay = QVBoxLayout(sidebar); side_lay.setContentsMargins(10, 30, 10, 30)
        
        self.btn_prof = QPushButton("  User Profile"); self.btn_prof.setStyleSheet(SIDEBAR_BTN_STYLE + "background-color: #2D3748;"); self.btn_prof.setCursor(Qt.CursorShape.PointingHandCursor)
        side_lay.addWidget(self.btn_prof)
        
        self.btn_lang = QPushButton("  Language"); self.btn_lang.setStyleSheet(SIDEBAR_BTN_STYLE); self.btn_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang.clicked.connect(lambda: self.stack.setCurrentIndex(5)); side_lay.addWidget(self.btn_lang) 
        
        self.btn_news = QPushButton("  What's new"); self.btn_news.setStyleSheet(SIDEBAR_BTN_STYLE); side_lay.addWidget(self.btn_news)
        
        self.del_btn = QPushButton("  Delete Account"); self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet("background-color: transparent; color: #E53E3E; border: 1px solid #E53E3E; border-radius: 5px; padding: 10px; margin-top: 10px;")
        self.del_btn.clicked.connect(self.handle_delete_account); side_lay.addWidget(self.del_btn)

        side_lay.addStretch()
        self.logout_btn = QPushButton("  Log Out"); self.logout_btn.setFixedHeight(40); self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setStyleSheet("background-color: #FF0000; color: white; border-radius: 10px; font-weight: bold;")
        logout_icon = os.path.join(self.basedir, "assets", "logout.png")
        if os.path.exists(logout_icon): self.logout_btn.setIcon(QIcon(logout_icon))
        self.logout_btn.clicked.connect(self.handle_logout) 
        side_lay.addWidget(self.logout_btn)
        
        content = QFrame(); content.setStyleSheet("background-color: #1A202C; border-top-right-radius: 25px; border-bottom-right-radius: 25px;")
        c_lay = QVBoxLayout(content); c_lay.setContentsMargins(40, 30, 40, 40)
        header = QHBoxLayout()
        self.title_label = QLabel("Profile details"); self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); self.title_label.setStyleSheet("color: white; border-bottom: 2px solid white;")
        close_btn = QPushButton("✖"); close_btn.setFixedSize(25, 25); close_btn.setStyleSheet("color: white; background-color: #FF0000; border-radius: 12px;"); close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.title_label); header.addStretch(); header.addWidget(close_btn)
        self.avatar = QLabel("OP"); self.avatar.setFixedSize(80, 80); self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background-color: #CBD5E0; border-radius: 40px; color: #1A202C; font-weight: bold; font-size: 20px;")
        
        self.u_in = QLineEdit(); self.u_in.setStyleSheet(INPUT_STYLE); self.u_in.setReadOnly(True)
        self.e_in = QLineEdit(); self.e_in.setStyleSheet(INPUT_STYLE); self.e_in.setReadOnly(True)
        self.p_in = QLineEdit("**********"); self.p_in.setStyleSheet(INPUT_STYLE); self.p_in.setReadOnly(True)
        self.rp_in = QLineEdit(); self.rp_in.setPlaceholderText("Re-type Password"); self.rp_in.setStyleSheet(INPUT_STYLE)
        
        self.edit_btn = QPushButton("  Edit profile"); self.edit_btn.setFixedSize(130, 35); self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setStyleSheet("background-color: #0D3B66; color: white; border-radius: 15px; font-weight: bold;")
        edit_icon = os.path.join(self.basedir, "assets", "edit.png")
        if os.path.exists(edit_icon): self.edit_btn.setIcon(QIcon(edit_icon))
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        c_lay.addLayout(header); c_lay.addSpacing(20); c_lay.addWidget(self.avatar); c_lay.addSpacing(10)
        
        self.lbl_user = QLabel("Displayed Username"); self.lbl_user.setStyleSheet("color: #718096; font-size: 11px;")
        c_lay.addWidget(self.lbl_user)
        cont = QWidget(); cont.setStyleSheet(FIELD_CONTAINER_STYLE); l = QVBoxLayout(cont); l.setContentsMargins(0,0,0,0); l.addWidget(self.u_in); c_lay.addWidget(cont)

        self.lbl_email = QLabel("Email"); self.lbl_email.setStyleSheet("color: #718096; font-size: 11px;")
        c_lay.addWidget(self.lbl_email)
        cont = QWidget(); cont.setStyleSheet(FIELD_CONTAINER_STYLE); l = QVBoxLayout(cont); l.setContentsMargins(0,0,0,0); l.addWidget(self.e_in); c_lay.addWidget(cont)

        self.lbl_pass = QLabel("Password"); self.lbl_pass.setStyleSheet("color: #718096; font-size: 11px;")
        c_lay.addWidget(self.lbl_pass)
        cont = QWidget(); cont.setStyleSheet(FIELD_CONTAINER_STYLE); l = QVBoxLayout(cont); l.setContentsMargins(0,0,0,0); l.addWidget(self.p_in); c_lay.addWidget(cont)

        self.rp_lbl = QLabel("Re-type Password"); self.rp_lbl.setStyleSheet("color: #718096; font-size: 11px;"); self.rp_lbl.hide(); c_lay.addWidget(self.rp_lbl)
        self.rp_cont = QWidget(); self.rp_cont.setStyleSheet(FIELD_CONTAINER_STYLE); rl = QVBoxLayout(self.rp_cont); rl.setContentsMargins(0,0,0,0); rl.addWidget(self.rp_in); self.rp_cont.hide(); c_lay.addWidget(self.rp_cont)
        
        c_lay.addSpacing(20); c_lay.addWidget(self.edit_btn); c_lay.addStretch()
        main_layout.addWidget(sidebar); main_layout.addWidget(content)

    def update_translations(self, lang_code):
        self.btn_prof.setText(translate_text("  User Profile", lang_code))
        self.btn_lang.setText(translate_text("  Language", lang_code))
        self.btn_news.setText(translate_text("  What's new", lang_code))
        self.del_btn.setText(translate_text("  Delete Account", lang_code))
        self.logout_btn.setText(translate_text("  Log Out", lang_code))
        self.title_label.setText(translate_text("Profile details", lang_code))
        self.lbl_user.setText(translate_text("Displayed Username", lang_code))
        self.lbl_email.setText(translate_text("Email", lang_code))
        self.lbl_pass.setText(translate_text("Password", lang_code))
        self.rp_lbl.setText(translate_text("Re-type Password", lang_code))
        self.rp_in.setPlaceholderText(translate_text("Re-type Password", lang_code))
        
        if self.u_in.isReadOnly(): self.edit_btn.setText(translate_text("  Edit profile", lang_code))
        else: self.edit_btn.setText(translate_text("  Confirm Edit", lang_code))

    def update_profile_info(self, user):
        display_text = user['display_name'] if user['display_name'] else user['username']
        self.u_in.setText(display_text)
        self.e_in.setText(user['email'])
        self.user_email = user['email']
        self.avatar.setText(user['initials'] if user['initials'] else "??")

    def toggle_edit_mode(self):
        if self.u_in.isReadOnly():
            self.u_in.setReadOnly(False); self.p_in.setReadOnly(False); self.p_in.setText("")
            self.rp_lbl.show(); self.rp_cont.show(); self.edit_btn.setText("  Confirm Edit")
            self.edit_btn.setStyleSheet("background-color: #0F8E52; color: white; border-radius: 15px; font-weight: bold;")
        else:
            if not all([self.u_in.text(), self.p_in.text(), self.rp_in.text()]): QMessageBox.warning(self, "Error", "All fields required."); return
            if self.p_in.text() != self.rp_in.text(): QMessageBox.critical(self, "Error", "Passwords mismatch."); return
            update_password(self.user_email, self.p_in.text())
            update_display_name(self.user_email, self.u_in.text())
            QMessageBox.information(self, "Success", "Profile Updated! Please log in again.")
            self.stack.widget(0).clear_fields()
            self.stack.setCurrentIndex(0)

    def handle_logout(self):
        self.stack.widget(0).clear_fields()
        self.stack.setCurrentIndex(0)

    def handle_delete_account(self):
        reply = QMessageBox.question(self, 'Confirm', "Delete account permanently?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if delete_user_account(self.user_email): 
                QMessageBox.information(self, "Deleted", "Account removed.")
                self.stack.widget(0).clear_fields()
                self.stack.setCurrentIndex(0)

# --- MAIN WINDOW ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        create_db(); self.setFixedSize(1000, 750); self.setStyleSheet("background-color: #5D5E62;")
        self.stack = QStackedWidget(self)
        self.profile_page = UserProfilePage(self.stack)
        
        # Create LoginPage first (needed for LanguagePage reference)
        self.login_page = LoginPage(self.stack, self.profile_page, None)  
        self.language_page = LanguagePage(self.stack, self.login_page)  
        
        # Now update LoginPage with language_page reference
        self.login_page.language_page = self.language_page
        
        self.stack.addWidget(self.login_page)  # 0
        self.stack.addWidget(RegisterPage(self.stack))  # 1
        self.stack.addWidget(ForgotPasswordPage(self.stack))  # 2
        self.stack.addWidget(self.profile_page)  # 3
        self.stack.addWidget(ResetPasswordPage(self.stack))  # 4
        self.stack.addWidget(self.language_page)  # 5
        
        layout = QVBoxLayout(self); layout.addWidget(self.stack)

    # FIXED: Central method to update all pages from anywhere
    def update_all_pages(self, lang_code):
        for i in range(self.stack.count()):
            page = self.stack.widget(i)
            if hasattr(page, 'update_translations'):
                page.update_translations(lang_code)

def run_server():
    log = logging.getLogger('werkzeug'); log.setLevel(logging.ERROR); flask_app.run(port=5000, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())