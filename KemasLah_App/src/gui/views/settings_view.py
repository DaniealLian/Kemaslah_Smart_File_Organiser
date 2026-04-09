import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QLineEdit, QScrollArea,
                             QCheckBox, QButtonGroup, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush
from auth.authentication_page import translate_text


def parse_json_response(res):
    print("Status:", res.status_code)
    print("Response:", res.text)

    if not res.text or not res.text.strip():
        return None, "Server returned empty response."

    try:
        return res.json(), None
    except Exception:
        return None, f"Server returned invalid response:\n{res.text}"


# ── OTP Worker Thread ─────────────────────────────────────────────────────────
class OtpEmailWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, email):
        super().__init__()
        self.email = email

    def run(self):
        try:
            res = requests.post(
                "http://127.0.0.1:5000/request-otp",
                json={"email": self.email},
                timeout=20
            )

            data, error = parse_json_response(res)
            if error:
                self.finished.emit(False, error)
                return

            if res.status_code == 200:
                self.finished.emit(True, data.get("message", "OTP sent! Please check your inbox."))
            else:
                self.finished.emit(False, data.get("message", "Failed to send OTP."))

        except Exception as e:
            self.finished.emit(False, str(e))


# ── Avatar widget ─────────────────────────────────────────────────────────────
class AvatarWidget(QWidget):
    def __init__(self, initials="OP", size=70, parent=None):
        super().__init__(parent)
        self.initials = initials
        self.avatar_size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#4A5568")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.avatar_size, self.avatar_size)
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", int(self.avatar_size * 0.28), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.initials)


# ── Reusable labelled field ───────────────────────────────────────────────────
class LabeledInput(QWidget):
    def __init__(self, label, placeholder="", password=False, read_only=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #718096; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setReadOnly(read_only)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent; color: white; border: none;
                border-bottom: 1px dashed #4A5568; padding: 4px 0px; font-size: 13px;
            }
            QLineEdit:focus { border-bottom: 1px dashed #63B3ED; }
            QLineEdit:read-only { color: #A0AEC0; }
        """)
        layout.addWidget(self.input)

    def text(self):
        return self.input.text()

    def setText(self, text):
        self.input.setText(text)


# ── User Profile Panel ────────────────────────────────────────────────────────
class UserProfilePanel(QWidget):
    """
    Username: editable, saved to DB via API on confirm.
    Email:    always read-only — cannot be changed.
    Password: lives in its own ChangePasswordPanel (OTP flow).
    """

    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.edit_mode = False
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(14)

        title = QLabel("Profile Details")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;"
                            "border-bottom: 1px solid #4A5568; padding-bottom: 8px;")
        self.main_layout.addWidget(title)

        username = self.user_data.get('display_name') or self.user_data.get('username', 'Guest')
        initials = "".join(p[0].upper() for p in username.split()[:2]) or "OP"
        self.avatar = AvatarWidget(initials, 70)
        self.main_layout.addWidget(self.avatar)

        # Username — editable in edit mode
        self.username_field = LabeledInput("Displayed Username", read_only=True)
        self.username_field.setText(username)
        self.main_layout.addWidget(self.username_field)

        # Email — ALWAYS read-only, never unlocked
        self.email_field = LabeledInput("Email", read_only=True)
        self.email_field.setText(self.user_data.get('email', ''))
        self.main_layout.addWidget(self.email_field)

        lock_note = QLabel("🔒  Email cannot be changed")
        lock_note.setStyleSheet("color: #4A5568; font-size: 10px; background: transparent; border: none;")
        self.main_layout.addWidget(lock_note)

        self.action_btn = QPushButton("✏  Edit Username")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet(self._btn_style("#2D3748", "#3D4A5C", border="1px solid #4A5568"))
        self.action_btn.clicked.connect(self._toggle_edit)
        self.main_layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Account Deletion Action
        self.delete_btn = QPushButton("🗑 Delete Account")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet(self._btn_style("#742A2A", "#9B2C2C"))
        self.delete_btn.clicked.connect(self._handle_delete_account)
        self.main_layout.addWidget(self.delete_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addStretch()

    def _handle_delete_account(self):
        email = self.user_data.get("email", "").strip()

        if not email:
            QMessageBox.warning(self, "Error", "No user email found.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Account",
            "Are you sure you want to permanently delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            res = requests.post(
                "http://127.0.0.1:5000/profile/delete",
                json={"email": email},
                timeout=5
            )

            data, error = parse_json_response(res)
            if error:
                QMessageBox.critical(self, "Error", error)
                return

            if res.status_code == 200:
                QMessageBox.information(self, "Success", "Account deleted successfully.")

                main_window = self.window()
                if hasattr(main_window, "on_logout"):
                    main_window.on_logout()
                elif hasattr(main_window, "logout_requested"):
                    main_window.logout_requested.emit()
            else:
                QMessageBox.critical(self, "Error", data.get("message", "Failed to delete account."))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Server error: {e}")

    def _btn_style(self, bg, hover_bg, color="white", border="none"):
        return (f"QPushButton {{ background-color: {bg}; color: {color}; border: {border};"
                f" border-radius: 5px; padding: 8px 20px; font-size: 13px; }}"
                f"QPushButton:hover {{ background-color: {hover_bg}; }}")

    def _toggle_edit(self):
        if not self.edit_mode:
            self.edit_mode = True
            self.username_field.input.setReadOnly(False)
            self.username_field.input.setFocus()
            self.action_btn.setText("✓  Save Username")
            self.action_btn.setStyleSheet(self._btn_style("#276749", "#2F855A"))
        else:
            new_name = self.username_field.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Validation Error", "Username cannot be empty.")
                return

            email = self.user_data.get("email", "").strip()

            if not email:
                QMessageBox.warning(self, "Error", "No user email found.")
                return

            try:
                res = requests.post(
                    "http://127.0.0.1:5000/profile/update",
                    json={
                        "email": email,
                        "display_name": new_name,
                        "language_code": self.user_data.get("language_code", "en")
                    },
                    timeout=5
                )

                data, error = parse_json_response(res)
                if error:
                    QMessageBox.critical(self, "Error", error)
                    self.username_field.setText(
                        self.user_data.get("display_name") or self.user_data.get("username", "Guest")
                    )
                    self.edit_mode = False
                    self.username_field.input.setReadOnly(True)
                    self.action_btn.setText("✏  Edit Username")
                    self.action_btn.setStyleSheet(self._btn_style("#2D3748", "#3D4A5C", border="1px solid #4A5568"))
                    return

                if res.status_code == 200:
                    self.user_data["display_name"] = new_name
                    self.user_data["username"] = new_name
                    self.avatar.initials = "".join(p[0].upper() for p in new_name.split()[:2]) or "OP"
                    self.avatar.update()
                    QMessageBox.information(self, "Success", "Username updated successfully!")
                else:
                    QMessageBox.critical(self, "Error", data.get("message", "Failed to save. Please try again."))
                    self.username_field.setText(
                        self.user_data.get("display_name") or self.user_data.get("username", "Guest")
                    )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Server error: {e}")
                self.username_field.setText(
                    self.user_data.get("display_name") or self.user_data.get("username", "Guest")
                )

            self.edit_mode = False
            self.username_field.input.setReadOnly(True)
            self.action_btn.setText("✏  Edit Username")
            self.action_btn.setStyleSheet(self._btn_style("#2D3748", "#3D4A5C", border="1px solid #4A5568"))


# ── Change Password Panel (OTP flow) ─────────────────────────────────────────
class ChangePasswordPanel(QWidget):
    """
    Same 3-step flow as the Forgot Password login page:
      Step 1 — email shown read-only + "Request OTP" button
      Step 2 — OTP field + "Verify OTP" button  (shown after OTP sent)
      Step 3 — new password fields               (shown after OTP verified)
    """

    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.user_email = self.user_data.get('email', '')
        self.countdown = 60
        self.verified_otp = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(14)

        title = QLabel("Change Password")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;"
                            "border-bottom: 1px solid #4A5568; padding-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("An OTP will be sent to your registered email to verify "
                          "your identity before changing your password.")
        subtitle.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Email — always read-only
        self.email_field = LabeledInput("Your Email", read_only=True)
        self.email_field.setText(self.user_email)
        layout.addWidget(self.email_field)

        # Step 1: Request OTP
        self.req_btn = QPushButton("Request OTP")
        self.req_btn.setFixedHeight(38)
        self.req_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.req_btn.setStyleSheet("""
            QPushButton { background-color: #0D3B66; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1A4F80; }
            QPushButton:disabled { background-color: #2D3748; color: #718096; }
        """)
        self.req_btn.clicked.connect(self._handle_otp_request)
        layout.addWidget(self.req_btn)

        # Step 2: OTP entry (hidden until OTP sent)
        self.otp_section = QWidget()
        otp_lay = QVBoxLayout(self.otp_section)
        otp_lay.setContentsMargins(0, 0, 0, 0)
        otp_lay.setSpacing(10)
        self.otp_field = LabeledInput("Enter OTP", placeholder="6-digit code")
        otp_lay.addWidget(self.otp_field)
        self.verify_otp_btn = QPushButton("Verify OTP")
        self.verify_otp_btn.setFixedHeight(38)
        self.verify_otp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.verify_otp_btn.setStyleSheet("""
            QPushButton { background-color: #0F8E52; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1AA063; }
        """)
        self.verify_otp_btn.clicked.connect(self._handle_otp_verify)
        otp_lay.addWidget(self.verify_otp_btn)
        self.otp_section.setVisible(False)
        layout.addWidget(self.otp_section)

        # Step 3: New password fields (hidden until OTP verified)
        self.pw_section = QWidget()
        pw_lay = QVBoxLayout(self.pw_section)
        pw_lay.setContentsMargins(0, 0, 0, 0)
        pw_lay.setSpacing(10)
        verified_lbl = QLabel("✅  Identity verified. Enter your new password below.")
        verified_lbl.setStyleSheet("color: #68D391; font-size: 12px;")
        pw_lay.addWidget(verified_lbl)
        self.new_pw_field = LabeledInput("New Password", password=True)
        pw_lay.addWidget(self.new_pw_field)
        self.confirm_pw_field = LabeledInput("Re-enter New Password", password=True)
        pw_lay.addWidget(self.confirm_pw_field)
        self.save_pw_btn = QPushButton("Save New Password")
        self.save_pw_btn.setFixedHeight(38)
        self.save_pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_pw_btn.setStyleSheet("""
            QPushButton { background-color: #0D3B66; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1A4F80; }
        """)
        self.save_pw_btn.clicked.connect(self._handle_save_password)
        pw_lay.addWidget(self.save_pw_btn)
        self.pw_section.setVisible(False)
        layout.addWidget(self.pw_section)
        layout.addStretch()

        self.resend_timer = QTimer()
        self.resend_timer.timeout.connect(self._update_timer_text)

    def _handle_otp_request(self):
        if not self.user_email:
            QMessageBox.warning(self, "Error", "No email address found for this account.")
            return
        self.req_btn.setText("Sending...")
        self.req_btn.setEnabled(False)
        self.worker = OtpEmailWorker(self.user_email)
        self.worker.finished.connect(self._on_otp_sent)
        self.worker.start()

    def _on_otp_sent(self, success, message):
        if success:
            QMessageBox.information(self, "OTP Sent", message)
            self.otp_section.setVisible(True)
            self.countdown = 60
            self.resend_timer.start(1000)
        else:
            QMessageBox.critical(self, "Error", f"Failed to send OTP: {message}")
            self.req_btn.setText("Request OTP")
            self.req_btn.setEnabled(True)

    def _update_timer_text(self):
        if self.countdown > 0:
            self.req_btn.setText(f"Resend in {self.countdown}s")
            self.countdown -= 1
        else:
            self.resend_timer.stop()
            self.req_btn.setEnabled(True)
            self.req_btn.setText("Resend OTP")

    def _handle_otp_verify(self):
        otp = self.otp_field.text().strip()
        if not otp:
            QMessageBox.warning(self, "Validation Error", "Please enter the OTP code.")
            return
        try:
            res = requests.post(
                "http://127.0.0.1:5000/verify-otp",
                json={"email": self.user_email, "otp": otp},
                timeout=5
            )

            data, error = parse_json_response(res)
            if error:
                QMessageBox.critical(self, "Error", error)
                return

            if res.status_code == 200:
                self.verified_otp = otp
                self.otp_section.setVisible(False)
                self.pw_section.setVisible(True)
                self.req_btn.setVisible(False)
            else:
                QMessageBox.critical(self, "Error", data.get("message", "Invalid or expired OTP. Please try again."))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Server error: {e}")

    def _handle_save_password(self):
        import re
        new_pw = self.new_pw_field.text()
        confirm_pw = self.confirm_pw_field.text()
        if not new_pw or not confirm_pw:
            QMessageBox.warning(self, "Validation Error", "Both password fields are required.")
            return
        if new_pw != confirm_pw:
            QMessageBox.critical(self, "Error", "Passwords do not match.")
            return
        if not re.match(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$', new_pw
        ):
            QMessageBox.critical(self, "Weak Password",
                "Password must be at least 10 characters and include:\n"
                "• Uppercase & lowercase letters\n"
                "• A number\n"
                "• A special character (@$!%*?&)")
            return
        try:
            res = requests.post(
                "http://127.0.0.1:5000/reset-password",
                json={
                    "email": self.user_email,
                    "otp": self.verified_otp,
                    "new_password": new_pw
                },
                timeout=5
            )

            data, error = parse_json_response(res)
            if error:
                QMessageBox.critical(self, "Error", error)
                return

            if res.status_code == 200:
                QMessageBox.information(self, "Success", "Password changed successfully!")
                self._reset_panel()
            else:
                QMessageBox.critical(self, "Error", data.get("message", "Failed to change password."))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Server error: {e}")

    def _reset_panel(self):
        self.otp_field.setText("")
        self.new_pw_field.setText("")
        self.confirm_pw_field.setText("")
        self.otp_section.setVisible(False)
        self.pw_section.setVisible(False)
        self.req_btn.setVisible(True)
        self.req_btn.setText("Request OTP")
        self.req_btn.setEnabled(True)
        self.resend_timer.stop()


# Language Panel
class LanguagePanel(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.user_email = user_data.get('email', 'guest@local')

        current_lang_code = user_data.get('language_code', 'en')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        title = QLabel("Language")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;"
                            "border-bottom: 1px solid #4A5568; padding-bottom: 8px;")
        layout.addWidget(title)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        languages = [
            (1, "English", "en"),
            (2, "Bahasa Melayu", "ms"),
            (3, "Chinese (Simplified)", "zh-CN"),
            (4, "Tamil", "ta")
        ]

        for lang_id, lang_name, lang_code in languages:
            cb = QCheckBox(lang_name)

            if lang_code == current_lang_code:
                cb.setChecked(True)

            cb.setStyleSheet("""
                QCheckBox { color: white; font-size: 13px; padding: 10px 0px; border-bottom: 1px solid #2D3748; }
                QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #4A5568; border-radius: 3px; }
                QCheckBox::indicator:checked { background-color: #3182CE; border-color: #3182CE; }
            """)
            cb.clicked.connect(lambda checked, lid=lang_id, lcode=lang_code: self._change_language(lid, lcode))
            self.btn_group.addButton(cb, lang_id)
            layout.addWidget(cb)

        layout.addStretch()

    def _change_language(self, lang_id, lang_code):
        try:
            display_name = (
                self.user_data.get("display_name")
                or self.user_data.get("username")
                or self.user_email.split("@")[0]
            )

            res = requests.post(
                "http://127.0.0.1:5000/profile/update",
                json={
                    "email": self.user_email,
                    "display_name": display_name,
                    "language_code": lang_code
                },
                timeout=5
            )

            data, error = parse_json_response(res)
            if error:
                QMessageBox.critical(self, "Error", error)
                return

            if res.status_code == 200:
                self.user_data["language_code"] = lang_code
                self.user_data["display_name"] = display_name
                if not self.user_data.get("username"):
                    self.user_data["username"] = display_name

                main_window = self.window()
                if hasattr(main_window, "update_all_pages"):
                    main_window.update_all_pages(lang_code)
            else:
                QMessageBox.critical(self, "Error", data.get("message", "Failed to update language."))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Server error: {e}")


# ── What's New Panel ──────────────────────────────────────────────────────────
class WhatsNewPanel(QWidget):
    def __init__(self, updates=None):
        super().__init__()
        self.updates = updates or [
            "Bahasa Melayu Language option has been added to application language",
        ]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        title = QLabel("What's New")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;"
                            "border-bottom: 1px solid #4A5568; padding-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("List of what has been added in the most recent update")
        subtitle.setStyleSheet("color: #A0AEC0; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        for item in self.updates:
            row = QHBoxLayout()
            bullet = QLabel("•")
            bullet.setStyleSheet("color: #A0AEC0; font-size: 14px;")
            bullet.setFixedWidth(16)
            text = QLabel(item)
            text.setStyleSheet("color: #E2E8F0; font-size: 13px;")
            text.setWordWrap(True)
            row.addWidget(bullet, alignment=Qt.AlignmentFlag.AlignTop)
            row.addWidget(text)
            layout.addLayout(row)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #2D3748;")
            layout.addWidget(sep)

        layout.addStretch()


# ── Main Settings View ────────────────────────────────────────────────────────
class SettingsView(QWidget):
    closed = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {"username": "Guest", "email": "guest@local"}
        self.is_guest = self.user_data.get('email') == 'guest@local'
        self.init_ui()

    def init_ui(self):
        self.setObjectName("SettingsOverlay")
        self.setStyleSheet("#SettingsOverlay { background-color: rgba(0, 0, 0, 180); }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setFixedSize(620, 440)
        container.setStyleSheet(
            "QFrame { background-color: #1A202C; border-radius: 12px; border: 1px solid #2D3748; }")

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(165)
        sidebar.setStyleSheet(
            "QFrame { background-color: #171E2B; border-top-left-radius: 12px;"
            " border-bottom-left-radius: 12px; border: none; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 12, 0, 12)
        sidebar_layout.setSpacing(0)

        self._sidebar_buttons = {}
        for label in ["User Profile", "Change Password", "Language", "What's new"]:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.setStyleSheet(self._sidebar_btn_style(False))
            btn.clicked.connect(lambda checked, l=label: self._switch_panel(l))
            sidebar_layout.addWidget(btn)
            self._sidebar_buttons[label] = btn

        sidebar_layout.addStretch()

        logout_btn = QPushButton("  ⏻  Log Out")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet(
            "QPushButton { background-color: #C53030; color: white; border: none;"
            " border-radius: 18px; font-size: 12px; font-weight: bold; margin: 8px 16px; }"
            "QPushButton:hover { background-color: #E53E3E; }")
        logout_btn.clicked.connect(self.logout_requested.emit)
        sidebar_layout.addWidget(logout_btn)
        container_layout.addWidget(sidebar)

        # Right content
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 8, 8, 0)
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #C53030; color: white; border-radius: 14px;"
            " font-size: 12px; border: none; }"
            "QPushButton:hover { background-color: #E53E3E; }")
        close_btn.clicked.connect(self.closed.emit)
        close_row.addWidget(close_btn)
        right_layout.addLayout(close_row)

        self._panels = {
            "User Profile":    UserProfilePanel(self.user_data),
            "Change Password": ChangePasswordPanel(self.user_data),
            "Language":        LanguagePanel(self.user_data),
            "What's new":      WhatsNewPanel(),
        }

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; border: none; }")
        for panel in self._panels.values():
            scroll = QScrollArea()
            scroll.setWidget(panel)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            self._stack.addWidget(scroll)

        self._panel_index = {label: i for i, label in enumerate(self._panels)}
        right_layout.addWidget(self._stack)
        container_layout.addWidget(right_frame)
        outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        self._switch_panel("User Profile")

    def _sidebar_btn_style(self, active: bool) -> str:
        if active:
            return ("QPushButton { background-color: #1A202C; color: white; border: none;"
                    " border-left: 3px solid #3182CE; text-align: left;"
                    " padding-left: 16px; font-size: 13px; font-weight: bold; }")
        return ("QPushButton { background-color: transparent; color: #A0AEC0; border: none;"
                " text-align: left; padding-left: 19px; font-size: 13px; }"
                "QPushButton:hover { color: white; background-color: #1E2733; }")

    def _switch_panel(self, label: str):
        for lbl, btn in self._sidebar_buttons.items():
            btn.setChecked(lbl == label)
            btn.setStyleSheet(self._sidebar_btn_style(lbl == label))
        idx = self._panel_index.get(label)
        if idx is not None:
            self._stack.setCurrentIndex(idx)

    def update_translations(self, lang_code):
        """Update language for all text in the Settings view."""
        try:
            from auth.authentication_page import translate_text
            for lbl, btn in self._sidebar_buttons.items():
                btn.setText(translate_text(lbl, lang_code))
        except Exception:
            pass