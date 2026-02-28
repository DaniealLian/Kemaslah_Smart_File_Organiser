import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import pyqtSignal, QDir, QSize

class TopBar(QWidget):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.init_ui()
        
    def init_ui(self):
        # Main horizontal layout for the TopBar
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(0)  # Remove extra spacing between the three main zones
        
        # LEFT ZONE: Breadcrumbs
        self.breadcrumb_layout = QHBoxLayout()
        self.breadcrumb_layout.setSpacing(5)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the breadcrumb layout to the main layout
        layout.addLayout(self.breadcrumb_layout)
        
        # MIDDLE ZONE: The Spacer
        layout.addStretch(1) 
        
        # RIGHT ZONE: Search Bar
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Name, email, etc...")
        search_input.setFixedWidth(250)

        # 1. Create the Search Action
        # Replace 'assets/search_icon.png' with your actual icon path
        search_icon_path = os.path.join(os.getcwd(), "assets", "search_icon.png")
        search_action = QAction(QIcon(search_icon_path), "Search", self)
        
        # 2. Use self. here as well
        search_input.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)

        # 3. Update CSS to give the text room so it doesn't overlap the icon
        search_input.setStyleSheet(""" 
            QLineEdit {
                padding: 8px 12px;
                padding-left: 35px; /* Extra padding on the left for the icon */
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: #E0E0E0;
            }
            QLineEdit:focus { border-color: #4A9EFF; }
        """)
        
        search_layout.addWidget(search_input)
        layout.addWidget(search_widget)
        self.setLayout(layout)

    def update_breadcrumbs(self, path):
        self.current_path = path
        
        # 1. Clear old buttons
        while self.breadcrumb_layout.count():
            child = self.breadcrumb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Handle Special Pages (Home, Settings, etc.)
        if path in ["Home", "Smart Archive", "Settings"] or not os.path.isabs(path):
            self.add_crumb_label(path)
            return

        # 3. Handle Real File Paths (e.g., C:/Users/Docs)
        path = os.path.normpath(path)
        parts = path.split(os.sep)
        
        current_build_path = ""
        
        for i, part in enumerate(parts):
            if not part: continue # skip empty
            
            # Windows drive fix (e.g., "C:") needs a slash to be valid
            if i == 0 and ':' in part:
                current_build_path = part + os.sep
            else:
                current_build_path = os.path.join(current_build_path, part)
            
            # Add Button
            self.add_crumb_button(part, current_build_path)
            
            # Add Separator ">" (except for the last item)
            if i < len(parts) - 1:
                sep = QLabel(">")
                sep.setStyleSheet("color: #666666; font-weight: bold;")
                self.breadcrumb_layout.addWidget(sep)

    def add_crumb_button(self, text, full_path):
        btn = QPushButton(text)
        # Store the path properly so the lambda captures the specific path for this button
        btn.clicked.connect(lambda checked, p=full_path: self.path_changed.emit(p))
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #C0C0C0;
                border: none;
                font-weight: bold;
                padding: 2px 5px;
            }
            QPushButton:hover {
                color: #4A9EFF;
                background-color: #2D3748;
                border-radius: 4px;
            }
        """)
        self.breadcrumb_layout.addWidget(btn)

    def add_crumb_label(self, text):
        """Used for static pages like Home where you can't click back"""
        label = QLabel(text)
        label.setStyleSheet("color: #C0C0C0; font-weight: bold; font-size: 14px; padding-left: 5px;")
        self.breadcrumb_layout.addWidget(label)