from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

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
    logout_requested = pyqtSignal()  # ADDED this
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.init_ui()

    def set_user_data(self, user_data):
        """Update sidebar with user information"""
        self.user_data = user_data
        
        # Update profile display
        display_name = user_data.get('display_name') or user_data.get('username', 'User')
        email = user_data.get('email', '')
        initials = user_data.get('initials', 'U')

        # Actually update the visible labels
        self.title_label.setText(display_name)
        self.desc_label.setText(email)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)
        
        # Profile section
        profile_widget = QWidget()
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(20, 10, 20, 20)
        
        self.profile_pic = CircularImage(40)
        # If you want to show initials:
        # self.profile_pic.setText(self.user_data.get('initials', 'U'))
        profile_layout.addWidget(self.profile_pic)
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        
        self.title_label = QLabel(self.user_data.get('display_name', 'User'))
        self.title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        
        self.desc_label = QLabel(self.user_data.get('email', 'user@example.com'))
        self.desc_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        profile_info.addWidget(self.title_label)
        profile_info.addWidget(self.desc_label)
        profile_layout.addLayout(profile_info)
        
        # Sign out icon
        signout_btn = QPushButton("→")
        signout_btn.setFixedSize(30, 30)
        signout_btn.setStyleSheet("""
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
        signout_btn.clicked.connect(self.logout_requested.emit)  # CONNECT THIS
        profile_layout.addWidget(signout_btn)
        
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
        pass
    
    def on_nav_clicked(self, button):
        for btn in self.nav_buttons:
            if btn != button:
                btn.setChecked(False)
        
        # Emit signal with identifier
        identifier = button.property("identifier")
        self.navigation_changed.emit(identifier)