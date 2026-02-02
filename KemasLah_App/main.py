import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QVBoxLayout
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from src.gui.widgets.sidebar import Sidebar
from src.gui.widgets.topbar import TopBar
from src.gui.widgets.actionbar import ActionBar
from src.gui.views.home_view import HomeView
from src.gui.views.file_browser_view import FileBrowserView
from src.gui.views.archive_view import ArchiveView
from src.gui.views.statistics_view import StatisticsView


class SmartFileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart File Manager")
        self.resize(1200, 800)
        
        # 1. Main Container (Holds everything)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Use HBox to put Sidebar (Left) next to Content (Right)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 2. Sidebar (Left Side)
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self.switch_view)
        main_layout.addWidget(self.sidebar)
        
        # 3. Right Panel Container (Right Side)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # --- GLOBAL HEADER ---
        self.top_bar = TopBar()
        self.top_bar.path_changed.connect(self.on_topbar_nav) # Connect breadcrumbs
        right_layout.addWidget(self.top_bar)
        
        self.action_bar = ActionBar(True, "Smart Organise")
        self.action_bar.action_clicked.connect(self.handle_action_bar)
        self.action_bar.smart_organise_clicked.connect(self.handle_smart_organise)
        right_layout.addWidget(self.action_bar)
        # ---------------------
        
        # 4. Content Area (The pages that change)
        self.stack = QStackedWidget()
        
        self.home_view = HomeView()
        self.files_view = FileBrowserView()
        self.archive_view = ArchiveView()
        self.statistics_view = StatisticsView()
        
        # Connect the File Browser to update the Top Bar
        self.files_view.path_changed.connect(self.top_bar.update_breadcrumbs)
        
        self.stack.addWidget(self.home_view)    # Index 0
        self.stack.addWidget(self.files_view)   # Index 1
        self.stack.addWidget(self.archive_view) # Index 2
        self.stack.addWidget(self.statistics_view) # Index 3
        
        right_layout.addWidget(self.stack)
        
        # Add the right panel to the main layout
        main_layout.addWidget(right_panel)

    def handle_action_bar(self, action_name):
        """Passes the action to the currently active view"""
        current_widget = self.stack.currentWidget()
        
        # We only want these buttons to work if we are in the File Browser
        if current_widget == self.files_view:
            # We access the table directly or via a wrapper method
            self.files_view.file_table.perform_action(action_name)

    def handle_smart_organise(self):
        """Placeholder for Smart Organise Logic"""
        current_widget = self.stack.currentWidget()
        if current_widget == self.files_view:
             # Just a basic demo of functionality
             from PyQt6.QtWidgets import QMessageBox
             QMessageBox.information(self, "Smart Organise", 
                 "This feature would now scan and sort files.\n(Functionality connected successfully!)")
             
    def switch_view(self, identifier):
        if identifier == "home":
            self.stack.setCurrentWidget(self.home_view)
            self.top_bar.update_breadcrumbs("Home")
            
        elif identifier == "files":
            self.stack.setCurrentWidget(self.files_view)
            self.top_bar.update_breadcrumbs(self.files_view.current_path)
            
        elif identifier == "archive":
            self.stack.setCurrentWidget(self.archive_view)
            self.top_bar.update_breadcrumbs("Smart Archive")

        elif identifier == "statistics":
            self.stack.setCurrentWidget(self.statistics_view)
            self.top_bar.update_breadcrumbs("Statistics")

    def on_topbar_nav(self, path):
        # Only navigate if we are currently looking at the file browser
        if self.stack.currentWidget() == self.files_view:
            self.files_view.on_breadcrumb_clicked(path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartFileManager()
    window.show()
    sys.exit(app.exec())