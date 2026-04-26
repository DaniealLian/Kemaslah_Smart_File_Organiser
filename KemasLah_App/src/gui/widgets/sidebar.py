import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, QSize,Qt
from PyQt6.QtGui import QIcon, QFontMetrics
from auth.authentication_page import translate_text

class CircularImage(QLabel):
    def __init__(self, size=50):
        super().__init__()
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #4A9EFF;
                border-radius: {size//2}px;
            }}
        """)


class Sidebar(QWidget):
    # Signal to communicate with main window
    navigation_changed = pyqtSignal(str)
    logout_requested = pyqtSignal()
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.init_ui()

    def set_user_data(self, user_data):
        """Update sidebar with user information and elide long emails"""
        self.user_data = user_data
        
        display_name = user_data.get('display_name') or user_data.get('username', 'User')
        email = user_data.get('email', '')

        self.title_label.setText(display_name)
        
        # Apply eliding logic to the new email
        metrics = QFontMetrics(self.desc_label.font())
        # Use the same 140px limit as in init_ui
        elided_email = metrics.elidedText(email, Qt.TextElideMode.ElideRight, 140)
        
        self.desc_label.setText(elided_email)
        self.desc_label.setToolTip(email)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)
        
        # Profile section
        profile_widget = QWidget()
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(20, 10, 20, 20)
        
        self.profile_pic = CircularImage(40)
        profile_layout.addWidget(self.profile_pic)
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        
        self.title_label = QLabel(self.user_data.get('display_name', 'User'))
        self.title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        
        # Get the email and define a pixel limit (e.g., 140px)
        email_text = self.user_data.get('email', 'user@example.com')
        limit = 140 

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        # Calculate and set elided text
        metrics = QFontMetrics(self.desc_label.font())
        elided_email = metrics.elidedText(email_text, Qt.TextElideMode.ElideRight, limit)
        
        self.desc_label.setText(elided_email)
        self.desc_label.setToolTip(email_text)
        
        profile_info.addWidget(self.title_label)
        profile_info.addWidget(self.desc_label)
        profile_layout.addLayout(profile_info)
        
        # Sign out icon
        self.signout_btn = QPushButton()
        self.signout_btn.setFixedSize(30, 30)

        icon_path = os.path.join(os.getcwd(), "assets", "logout.png")
        self.signout_btn.setIcon(QIcon(icon_path))
        self.signout_btn.setIconSize(QSize(30, 30))

        self.signout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF4444;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.1);
            }
        """)
        self.signout_btn.clicked.connect(self.logout_requested.emit)  # CONNECT THIS
        profile_layout.addWidget(self.signout_btn)
        
        profile_widget.setLayout(profile_layout)
        layout.addWidget(profile_widget)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("Home", "home"),
            ("All Files", "files"),
            ("Auto Archive", "archive"),
            ("File Sharing", "sharing"),
            ("Statistics", "statistics"),
            ("Settings", "settings")
        ]
        
        for text, identifier in nav_items:
            btn = QPushButton(text)
            btn.setProperty("identifier", identifier)
            btn.setProperty("base_text", text)
            btn.setCheckable(True)

            is_submenu = text.startswith("  ")
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 20px;
                    padding-left: {'40px' if is_submenu else '20px'};
                    border: none;
                    background-color: transparent;
                    color: #C0C0C0;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #3A3A4A;
                    color: #FFFFFF;
                }}
                QPushButton:checked {{
                    background-color: #4A5568;
                    color: #FFFFFF;
                }}
            """)
            
            btn.clicked.connect(lambda checked, b=btn: self.on_nav_clicked(b))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Set home as default
        self.nav_buttons[0].setChecked(True)
        
    
    def on_nav_clicked(self, button):
        for btn in self.nav_buttons:
            if btn != button:
                btn.setChecked(False)
        
        # Emit signal with identifier
        identifier = button.property("identifier")
        self.navigation_changed.emit(identifier)
    
    def set_active(self, identifier):
        """Programmatically highlights a specific sidebar button by its identifier"""
        for btn in self.nav_buttons:
           
            if btn.property("identifier") == identifier:
                btn.setChecked(True)
            
            else:
                btn.setChecked(False)

    def update_translations(self, lang_code):
        """Translates all sidebar navigation items"""
        for btn in self.nav_buttons:
            base_text = btn.property("base_text")
            
            # Strip whitespace, translate, then restore any visual indentation
            is_submenu = base_text.startswith("  ")
            clean_text = base_text.strip()
            
            translated_text = translate_text(clean_text, lang_code)
            
            if is_submenu:
                btn.setText(f"  {translated_text}")
            else:
                btn.setText(translated_text)