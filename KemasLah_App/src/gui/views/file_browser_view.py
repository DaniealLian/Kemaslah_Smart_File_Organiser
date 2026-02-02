import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QDir, pyqtSignal

from src.gui.widgets.file_table import FileTableWidget

class FileBrowserView(QWidget):
    path_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.home_path = QDir.homePath()
        self.current_path = self.home_path
        self.init_ui()
        self.navigate_to(self.home_path)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # File Table
        self.file_table = FileTableWidget()
        self.file_table.folder_opened.connect(self.navigate_to)
        layout.addWidget(self.file_table)
        
        self.setLayout(layout)

    def navigate_to(self, path):
        path = os.path.normpath(path)
        
        if not path.startswith(os.path.normpath(self.home_path)):
            path = self.home_path
            
        self.current_path = path
        self.file_table.load_files(path)
        
        self.path_changed.emit(path)

    def on_breadcrumb_clicked(self, path):
        self.navigate_to(path)