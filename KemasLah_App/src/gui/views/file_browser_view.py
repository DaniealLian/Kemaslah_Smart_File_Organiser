import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QDir

# Ensure these imports point to your correct folder locations
from src.gui.widgets.topbar import TopBar
from src.gui.widgets.actionbar import ActionBar
from src.gui.widgets.file_table import FileTableWidget

class FileBrowserView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Start at User Home Directory
        self.home_path = QDir.homePath()
        self.current_path = self.home_path
        
        self.init_ui()
        
        # Load the initial data
        self.navigate_to(self.home_path)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Top Bar (Breadcrumbs)
        self.top_bar = TopBar()
        self.top_bar.path_changed.connect(self.navigate_to) # Connect signal
        layout.addWidget(self.top_bar)
        
        # 2. Action Bar
        layout.addWidget(ActionBar(True, "Smart Organise"))
        
        # 3. File Table (Real Data)
        self.file_table = FileTableWidget()
        self.file_table.folder_opened.connect(self.navigate_to) # Connect signal
        layout.addWidget(self.file_table)
        
        self.setLayout(layout)

    def navigate_to(self, path):
        """Updates the view to show the target directory"""
        path = os.path.normpath(path)
        
        # Security Sandbox: Don't allow going above Home Directory
        # (Optional: remove this if you want full PC access)
        if not path.startswith(os.path.normpath(self.home_path)):
            path = self.home_path
            
        self.current_path = path
        
        # Update UI Components
        self.top_bar.update_breadcrumbs(path)
        self.file_table.load_files(path)