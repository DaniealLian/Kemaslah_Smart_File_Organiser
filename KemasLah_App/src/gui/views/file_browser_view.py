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

        self.history_back = []
        self.history_forward = []

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

    def navigate_to(self, path, is_history_nav=False):
        path = os.path.normpath(path)
        
        if not path.startswith(os.path.normpath(self.home_path)):
            path = self.home_path

        if self.current_path and self.current_path != path and not is_history_nav:
            self.history_back.append(self.current_path)
            self.history_forward.clear() # Clear forward history when making a new move
            
        self.current_path = path
        self.file_table.load_files(path)
        
        self.path_changed.emit(path)

    def on_breadcrumb_clicked(self, path):
        self.navigate_to(path)
    
    def go_back(self):
        if self.history_back:
            # Save current to forward history, then pop the last back path
            self.history_forward.append(self.current_path)
            prev_path = self.history_back.pop()
            self.navigate_to(prev_path, is_history_nav=True)

    def go_forward(self):
        if self.history_forward:
            # Save current to back history, then pop the next forward path
            self.history_back.append(self.current_path)
            next_path = self.history_forward.pop()
            self.navigate_to(next_path, is_history_nav=True)