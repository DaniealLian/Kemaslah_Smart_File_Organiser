import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import pyqtSignal, QDir

class TopBar(QWidget):
    # Signal: When a breadcrumb button is clicked, tell the main view to go there
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Breadcrumb Container
        self.breadcrumb_layout = QHBoxLayout()
        self.breadcrumb_layout.setSpacing(5)
        
        # Search bar (Keep existing style)
        search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("Search")
        search_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Name, email, etc...")
        search_input.setFixedWidth(250)
        search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: #E0E0E0;
            }
            QLineEdit:focus { border-color: #4A9EFF; }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        search_widget.setLayout(search_layout)
        
        layout.addLayout(self.breadcrumb_layout)
        layout.addStretch()
        layout.addWidget(search_widget)
        self.setLayout(layout)

    def update_breadcrumbs(self, path):
        """Rebuilds the breadcrumb buttons based on the current path"""
        self.current_path = path
        
        # Clear old buttons
        while self.breadcrumb_layout.count():
            child = self.breadcrumb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Normalize path for splitting
        path = os.path.normpath(path)
        parts = path.split(os.sep)

        # Reconstruct path step-by-step for the buttons
        reconstructed_path = parts[0] # Drive letter (e.g., C:)
        
        # Create Home/Drive Button
        self.add_crumb_button("🏠", reconstructed_path)

        # Loop through the rest of the folders
        for part in parts[1:]:
            if not part: continue # Skip empty splits
            reconstructed_path = os.path.join(reconstructed_path, part)
            
            # Add Separator
            sep = QLabel(">")
            sep.setStyleSheet("color: #888888;")
            self.breadcrumb_layout.addWidget(sep)
            
            # Add Folder Button
            self.add_crumb_button(part, reconstructed_path)

    def add_crumb_button(self, text, path_data):
        """Helper to create a styled breadcrumb button"""
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #C0C0C0;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover { color: #4A9EFF; text-decoration: underline; }
        """)
        # Connect click to signal
        btn.clicked.connect(lambda: self.path_changed.emit(path_data))
        self.breadcrumb_layout.addWidget(btn)