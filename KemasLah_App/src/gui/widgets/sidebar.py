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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)
        
        # Profile section
        profile_widget = QWidget()
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(20, 10, 20, 20)
        
        profile_pic = CircularImage(40)
        profile_layout.addWidget(profile_pic)
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        title_label = QLabel("Title")
        title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #888888; font-size: 11px;")
        profile_info.addWidget(title_label)
        profile_info.addWidget(desc_label)
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
    
    def set_active_by_identifier(self, identifier):
        """Programmatically set which navigation button is active"""
        for btn in self.nav_buttons:
            if btn.property("identifier") == identifier:
                btn.setChecked(True)
            else:
                btn.setChecked(False)