from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QLineEdit, QScrollArea,
                             QCheckBox, QButtonGroup, QSizePolicy, QSpacerItem,
                             QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush


# ── Avatar widget (circle with initials) ────────────────────────────────────
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


# ── Reusable field label + input ─────────────────────────────────────────────
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
                background: transparent;
                color: white;
                border: none;
                border-bottom: 1px dashed #4A5568;
                padding: 4px 0px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-bottom: 1px dashed #63B3ED;
            }
            QLineEdit:read-only {
                color: #A0AEC0;
            }
        """)
        layout.addWidget(self.input)

    def text(self):
        return self.input.text()

    def setText(self, text):
        self.input.setText(text)


# ── Content panels ────────────────────────────────────────────────────────────
class UserProfilePanel(QWidget):
    """Shows profile details; supports view and edit modes."""

    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.edit_mode = False
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(14)

        # Title
        title = QLabel("Profile details")
        title.setStyleSheet("""
            color: white; font-size: 16px; font-weight: bold;
            border-bottom: 1px solid #4A5568; padding-bottom: 8px;
        """)
        self.main_layout.addWidget(title)

        # Avatar
        username = (self.user_data.get('username')
                    or self.user_data.get('display_name', 'Guest'))
        initials = "".join(p[0].upper() for p in username.split()[:2]) or "OP"
        avatar = AvatarWidget(initials, 70)
        self.main_layout.addWidget(avatar)

        # Fields
        self.username_field = LabeledInput("Displayed Username", read_only=True)
        self.username_field.setText(username)
        self.main_layout.addWidget(self.username_field)

        email = (self.user_data.get('email', ''))
        self.email_field = LabeledInput("Email", read_only=True)
        self.email_field.setText(email)
        self.main_layout.addWidget(self.email_field)

        # Password row (single in view mode, split in edit mode)
        self.password_row = QHBoxLayout()
        self.password_row.setSpacing(10)
        self.password_field = LabeledInput("Password", password=True, read_only=True)
        self.password_field.setText("placeholder_pw")
        self.password_row.addWidget(self.password_field)
        self.main_layout.addLayout(self.password_row)

        # Re-type password (hidden until edit mode)
        self.retype_field = LabeledInput("Re-type Password", password=True)
        self.retype_field.setText("placeholder_pw")
        self.retype_field.setVisible(False)

        # Action button
        self.action_btn = QPushButton("✏  Edit profile")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D3748;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #3D4A5C; }
        """)
        self.action_btn.clicked.connect(self._toggle_edit)
        self.main_layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addStretch()

    def _toggle_edit(self):
        self.edit_mode = not self.edit_mode

        if self.edit_mode:
            # Switch to edit mode
            self.username_field.input.setReadOnly(False)
            self.email_field.input.setReadOnly(False)
            self.password_field.input.setReadOnly(False)

            # Show re-type field side-by-side with password
            self.password_row.addWidget(self.retype_field)
            self.retype_field.setVisible(True)

            self.action_btn.setText("✓  Confirm Edit")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #276749;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 20px;
                    font-size: 13px;
                }
                QPushButton:hover { background-color: #2F855A; }
            """)
        else:
            # Confirm / back to view mode
            self.username_field.input.setReadOnly(True)
            self.email_field.input.setReadOnly(True)
            self.password_field.input.setReadOnly(True)

            self.retype_field.setVisible(False)
            self.password_row.removeWidget(self.retype_field)

            self.action_btn.setText("✏  Edit profile")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D3748;
                    color: white;
                    border: 1px solid #4A5568;
                    border-radius: 5px;
                    padding: 8px 20px;
                    font-size: 13px;
                }
                QPushButton:hover { background-color: #3D4A5C; }
            """)


class LanguagePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        title = QLabel("Language")
        title.setStyleSheet("""
            color: white; font-size: 16px; font-weight: bold;
            border-bottom: 1px solid #4A5568; padding-bottom: 8px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Select a Language")
        subtitle.setStyleSheet("color: #A0AEC0; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for i, lang in enumerate(["English", "Chinese", "Bahasa Melayu"]):
            cb = QCheckBox(lang)
            cb.setChecked(i == 0)
            cb.setStyleSheet("""
                QCheckBox {
                    color: white;
                    font-size: 13px;
                    padding: 10px 0px;
                    border-bottom: 1px solid #2D3748;
                }
                QCheckBox::indicator {
                    width: 16px; height: 16px;
                    border: 1px solid #4A5568;
                    border-radius: 3px;
                    background: transparent;
                }
                QCheckBox::indicator:checked {
                    background-color: #3182CE;
                    border-color: #3182CE;
                    image: url(none);
                }
            """)
            self.btn_group.addButton(cb, i)
            layout.addWidget(cb)

        layout.addStretch()


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
        title.setStyleSheet("""
            color: white; font-size: 16px; font-weight: bold;
            border-bottom: 1px solid #4A5568; padding-bottom: 8px;
        """)
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

        # ── Dialog container ──────────────────────────────────────────────
        container = QFrame()
        container.setFixedSize(600, 420)
        container.setStyleSheet("""
            QFrame {
                background-color: #1A202C;
                border-radius: 12px;
                border: 1px solid #2D3748;
            }
        """)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ── Left sidebar ──────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #171E2B;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                border: none;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 12, 0, 12)
        sidebar_layout.setSpacing(0)

        self._sidebar_buttons = {}
        self._active_btn = None

        for label in ["User Profile", "Language", "What's new"]:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.setStyleSheet(self._sidebar_btn_style(False))
            btn.clicked.connect(lambda checked, l=label: self._switch_panel(l))
            sidebar_layout.addWidget(btn)
            self._sidebar_buttons[label] = btn

        sidebar_layout.addStretch()

        # Log Out button
        logout_btn = QPushButton("  ⏻  Log Out")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #C53030;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 12px;
                font-weight: bold;
                margin: 8px 16px;
            }
            QPushButton:hover { background-color: #E53E3E; }
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        sidebar_layout.addWidget(logout_btn)

        container_layout.addWidget(sidebar)

        # ── Right content area ────────────────────────────────────────────
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Close button (top-right)
        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 8, 8, 0)
        close_row.addStretch()
        close_btn = QPushButton("X")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #C53030;
                color: white;
                border-radius: 14px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { background-color: #E53E3E; }
        """)
        close_btn.clicked.connect(self.closed.emit)
        close_row.addWidget(close_btn)
        right_layout.addLayout(close_row)

        # Build panels once and store them in a QStackedWidget.
        # Never call setWidget() to swap them — QScrollArea takes ownership
        # and deletes the old widget, causing the "wrapped C++ object deleted" crash.
        self._panels = {
            "User Profile": UserProfilePanel(self.user_data),
            "Language":     LanguagePanel(),
            "What's new":   WhatsNewPanel(),
        }

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; border: none; }")

        for panel in self._panels.values():
            # Wrap each panel in its own scroll area so long content scrolls
            scroll = QScrollArea()
            scroll.setWidget(panel)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            self._stack.addWidget(scroll)

        # Map label -> stack index for fast switching
        self._panel_index = {label: i for i, label in enumerate(self._panels)}

        right_layout.addWidget(self._stack)
        container_layout.addWidget(right_frame)

        outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Activate default panel
        self._switch_panel("User Profile")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _sidebar_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #1A202C;
                    color: white;
                    border: none;
                    border-left: 3px solid #3182CE;
                    text-align: left;
                    padding-left: 16px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                color: #A0AEC0;
                border: none;
                text-align: left;
                padding-left: 19px;
                font-size: 13px;
            }
            QPushButton:hover { color: white; background-color: #1E2733; }
        """

    def _switch_panel(self, label: str):
        # Update sidebar button styles
        for lbl, btn in self._sidebar_buttons.items():
            btn.setChecked(lbl == label)
            btn.setStyleSheet(self._sidebar_btn_style(lbl == label))

        # Show the correct panel via index.
        # Never call setWidget() to swap panels into a QScrollArea —
        # it transfers ownership and deletes the old widget, causing the crash.
        idx = self._panel_index.get(label)
        if idx is not None:
            self._stack.setCurrentIndex(idx)