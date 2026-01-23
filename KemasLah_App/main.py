import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from widgets.sidebar import Sidebar
from views.file_browser_view import FileBrowserView
from views.archive_view import ArchiveView
from views.home_view import HomeView
from views.statistics_view import StatisticsView


class SmartFileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Smart File Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setStyleSheet("background-color: #1A202C;")
        main_layout.addWidget(self.sidebar)
        
        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #1A202C;")
        
        # Add views
        self.content_stack.addWidget(FileBrowserView())  # Index 0
        self.content_stack.addWidget(ArchiveView())      # Index 1
        self.content_stack.addWidget(HomeView())         # Index 2
        self.content_stack.addWidget(StatisticsView())   # Index 3
        
        main_layout.addWidget(self.content_stack)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Connect sidebar navigation
        self.sidebar.navigation_changed.connect(self.switch_view)
        
        # Set default view
        self.content_stack.setCurrentIndex(2)  # Home view
        
        self.setStyleSheet("QMainWindow { background-color: #1A202C; }")
    
    def switch_view(self, identifier):
        view_map = {
            "home": 2,
            "files": 0,
            "archive": 1,
            "statistics": 3
        }
        if identifier in view_map:
            self.content_stack.setCurrentIndex(view_map[identifier])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartFileManager()
    window.show()
    sys.exit(app.exec())