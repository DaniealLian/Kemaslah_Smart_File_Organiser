import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import pyqtSignal, QDir, QSize
from auth.authentication_page import translate_text

class TopBar(QWidget):
    path_changed = pyqtSignal(str)
    search_query_changed = pyqtSignal(str)
    refresh_clicked = pyqtSignal()  # Added from File 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.current_lang = "en" # Track current language
        self.init_ui()
        
    def init_ui(self):
        # Main horizontal layout for the TopBar
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(0) # Remove extra spacing between the three main zones
        
        # LEFT ZONE: Breadcrumbs
        self.breadcrumb_layout = QHBoxLayout()
        self.breadcrumb_layout.setSpacing(5)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the breadcrumb layout to the main layout
        layout.addLayout(self.breadcrumb_layout)
        
        # MIDDLE ZONE: The Spacer
        layout.addStretch(1)

        # REFRESH BUTTON: Added from File 1
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setToolTip("Refresh current view")
        self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D3748;
                color: #A0AEC0;
                border: 1px solid #4A5568;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #3D4A5C;
                color: #4A9EFF;
                border-color: #4A9EFF;
            }
            QPushButton:pressed {
                background-color: #1A2233;
            }
        """)
        layout.addWidget(self.refresh_btn)

        # RIGHT ZONE: Search Bar
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Name, email, etc...")
        self.search_input.setFixedWidth(250)

        # the Search Action
        search_icon_path = os.path.join(os.getcwd(), "assets", "search_icon.png")
        search_action = QAction(QIcon(search_icon_path), "Search", self)

        search_action.triggered.connect(self.emit_search)
        self.search_input.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.returnPressed.connect(self.emit_search)

        self.search_input.setStyleSheet(""" 
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
        
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_widget)
        self.setLayout(layout)

    def update_translations(self, lang_code):
        """Translates the top bar elements"""
        self.current_lang = lang_code
        
        # 1. Translate Search Bar Placeholder
        translated_placeholder = translate_text("Name, email, etc...", lang_code)
        self.search_input.setPlaceholderText(translated_placeholder)
        
        # 2. Refresh the breadcrumbs so static pages translate instantly
        if self.current_path:
            self.update_breadcrumbs(self.current_path)

    def update_breadcrumbs(self, path):
        self.current_path = path
        
        # 1. Clear old buttons
        while self.breadcrumb_layout.count():
            child = self.breadcrumb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Handle Special Pages (Home, Settings, etc.)
        if path in ["Home", "Smart Archive", "Settings", "Statistics"] or not os.path.isabs(path):
            translated_path = translate_text(path, getattr(self, 'current_lang', 'en'))
            self.add_crumb_label(translated_path)
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

    def emit_search(self):
        """Broadcasts the search text only when Enter is pressed or Icon is clicked"""
        self.search_query_changed.emit(self.search_input.text())