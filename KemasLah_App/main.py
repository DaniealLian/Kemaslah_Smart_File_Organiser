import sys
import threading
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtWidgets import QMessageBox

# Import authentication system
from auth.authentication_page import MainWindow as AuthWindow
from auth.server import app as flask_app
from auth.database import create_db

# Import your existing GUI components
from src.gui.widgets.sidebar import Sidebar
from src.gui.widgets.topbar import TopBar
from src.gui.widgets.actionbar import ActionBar
from src.gui.views.home_view import HomeView
from src.gui.views.file_browser_view import FileBrowserView
from src.gui.views.archive_view import ArchiveView
from src.gui.views.statistics_view import StatisticsView
from src.gui.views.settings_view import SettingsView
# Note: Settings view will use auth pages (UserProfilePage)


class SmartFileManager(QMainWindow):
    """Your existing file manager - now receives user_data and auth_window"""
    logout_requested = pyqtSignal()  # Signal to notify parent app of logout
    
    def __init__(self, user_data=None, auth_window=None):  # Added auth_window parameter
        super().__init__()
        self.user_data = user_data or {"username": "Guest", "email": "guest@local", "initials": "G"}
        self.auth_window = auth_window  # Store reference to auth window
        self.setWindowTitle("Kemaslah File Manager")
        self.resize(1200, 800)
        self.settings_overlay = None
        
        # 1. Main Container (Holds everything)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Use HBox to put Sidebar (Left) next to Content (Right)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 2. Sidebar (Left Side) - NOW with user data
        self.sidebar = Sidebar(user_data=self.user_data)
        self.sidebar.navigation_changed.connect(self.switch_view)
        self.sidebar.logout_requested.connect(self.handle_logout)
        main_layout.addWidget(self.sidebar)
        
        # 3. Right Panel Container (Right Side)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # --- GLOBAL HEADER ---
        self.top_bar = TopBar()
        self.top_bar.path_changed.connect(self.on_topbar_nav)
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
        # Listens for folder clicks
        self.home_view.folder_opened.connect(self.on_home_folder_opened)
        
        self.stack.addWidget(self.home_view)        # Index 0
        self.stack.addWidget(self.files_view)       # Index 1
        self.stack.addWidget(self.archive_view)     # Index 2
        self.stack.addWidget(self.statistics_view)  # Index 3
        # Index 4 will be auth window's profile page when settings is clicked
        
        right_layout.addWidget(self.stack)
        
        # Add the right panel to the main layout
        main_layout.addWidget(right_panel)
        
        # FIXED: Start on home view by default
        self.switch_view("home")

    def handle_logout(self):
        """Handle logout request from sidebar"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Logout', 
            'Are you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()

    def handle_action_bar(self, action_name):
        """Passes the action to the currently active view"""
        current_widget = self.stack.currentWidget()
        
        # We only want these buttons to work if we are in the File Browser
        if current_widget == self.files_view:
            self.files_view.file_table.perform_action(action_name)

    def handle_smart_organise(self):
        """Placeholder for Smart Organise Logic"""
        current_widget = self.stack.currentWidget()
        if current_widget == self.files_view:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Smart Organise", 
                "This feature would now scan and sort files.\n(Functionality connected successfully!)")
             
    def switch_view(self, identifier):

        if identifier == "settings":
            self.show_settings_overlay()
        else:
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
    
    def show_settings_overlay(self):
        if not self.settings_overlay:
            self.settings_overlay = SettingsView(self.user_data)
            self.settings_overlay.setParent(self) # Make it a child of the main window
            self.settings_overlay.closed.connect(self.hide_settings_overlay)
            self.settings_overlay.logout_requested.connect(self.handle_logout)
        
        # Resize to cover the whole window
        self.settings_overlay.resize(self.size())
        self.settings_overlay.show()
        self.settings_overlay.raise_()

    def hide_settings_overlay(self):
        if self.settings_overlay:
            self.settings_overlay.hide()

    # Ensure overlay resizes if the window resizes
    def resizeEvent(self, event):
        if self.settings_overlay and self.settings_overlay.isVisible():
            self.settings_overlay.resize(self.size())
        super().resizeEvent(event)
    
    def on_home_folder_opened(self, path):
        """Triggered when a user double-clicks a folder in the Home tab tables"""
        # 1. Tell the File Browser to load the specific folder path
        self.files_view.navigate_to(path)
        
        # 2. Switch the UI stack to show the files view
        self.switch_view("files")
        self.sidebar.set_active("files")


class KemaslahApp(QMainWindow):
    """Combined application with authentication + file manager"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize database
        create_db()
        
        # Set window properties
        self.setWindowTitle("Kemaslah - Smart File Manager")
        
        # Create stacked widget to hold auth and file manager
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Add authentication window (index 0)
        self.auth_window = AuthWindow()
        self.stack.addWidget(self.auth_window)
        
        # File manager will be created after successful login OR skip
        self.file_manager = None
        
        # Connect login success signal
        login_page = self.auth_window.stack.widget(0)
        if hasattr(login_page, 'login_successful'):
            login_page.login_successful.connect(self.on_login_success)
        else:
            print("WARNING: login_successful signal not found in LoginPage!")
            print("Make sure you've added the signal to auth/authentication_page.py")
        
        #Skip login become guest
        if hasattr(login_page, 'skip_login_clicked'):
            login_page.skip_login_clicked.connect(self.on_skip_login)
        
        # Start with auth screen size
        self.setFixedSize(1000, 750)
        
    def on_login_success(self, user_data):
        """Called when user successfully logs in"""
        print(f"Login successful for: {user_data.get('email')}")
        
        #This is to refresh the data so that no previous user data is displayed after logout
        if self.file_manager is not None:
            self.stack.removeWidget(self.file_manager)
            self.file_manager.deleteLater()
            self.file_manager = None

        self.file_manager = SmartFileManager(user_data, auth_window=self.auth_window)
        self.file_manager.logout_requested.connect(self.on_logout)
        self.stack.addWidget(self.file_manager)
        
        # Switch to file manager
        self.stack.setCurrentWidget(self.file_manager)
        self.file_manager.switch_view("home")
        
        # Resize window for file manager
        self.setMinimumSize(1200, 800)
        self.showMaximized()
    
    def on_skip_login(self):
        """Called when user skips login - use app as guest"""
        print("User chose to skip login (Guest mode)")
        
        # Create file manager with guest data
        guest_data = {
            "username": "Guest User",
            "email": "guest@local",
            "initials": "GU",
            "display_name": "Guest User"
        }
        
        if self.file_manager is None:
            self.file_manager = SmartFileManager(guest_data, auth_window=None)  # No auth window for guest
            # Don't connect logout in guest mode, or connect to a different handler
            self.file_manager.logout_requested.connect(self.on_guest_exit)
            self.stack.addWidget(self.file_manager)
        
        # Switch to file manager
        self.stack.setCurrentWidget(self.file_manager)
        
        self.file_manager.switch_view("home")
        
        # Resize window for file manager
        self.setMinimumSize(1200, 800)
        self.showMaximized()
    
    def on_guest_exit(self):
        """Handle return to login screen from guest mode"""

        reply = QMessageBox.question(
            self, 'Logout', 
            'Exit guest mode and return to login?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print("Returning to login screen from Guest mode...")
            
            # 1. Switch back to the auth window (index 0 in KemaslahApp stack)
            self.stack.setCurrentWidget(self.auth_window)
            
            # 2. Reset the auth window to the login page (index 0 in Auth stack)
            self.auth_window.stack.setCurrentIndex(0)
            
            # 3. Restore the login window dimensions
            self.setFixedSize(1000, 750)
            self.showNormal()
            
            # 4. Optional: Clear guest data from file_manager if it exists
            if self.file_manager:
                # We can either delete it to force a fresh start later or just leave it
                self.file_manager.deleteLater() 
                self.file_manager = None
                pass
    
    def on_logout(self):
        """Return to login screen"""
        print("Logging out...")

        # Destroy the file manager entirely so the next login rebuilds everything
        # from scratch — no stale user data anywhere (sidebar, settings overlay, etc.)
        if self.file_manager is not None:
            self.stack.removeWidget(self.file_manager)
            self.file_manager.deleteLater()
            self.file_manager = None
        
        # Clear login fields
        login_page = self.auth_window.stack.widget(0)
        if hasattr(login_page, 'clear_fields'):
            login_page.clear_fields()
        
        # Switch back to auth screen
        self.stack.setCurrentWidget(self.auth_window)
        
        # Restore auth window size
        self.setFixedSize(1000, 750)
        self.showNormal()
        
        # Show login page
        self.auth_window.stack.setCurrentIndex(0)

    def update_all_pages(self, lang_code):
        """
        Relays the translation update command to the auth window 
        and the file manager (if it exists).
        """
        # Update the authentication stack pages
        if hasattr(self.auth_window, 'update_all_pages'):
            self.auth_window.update_all_pages(lang_code)
        
        # Update the File Manager if the user is already inside the app
        if self.file_manager:
            # If you add an update_translations method to SmartFileManager later, 
            # call it here to change the Sidebar/Topbar language.
            pass


def run_server():
    """Run Flask server in background thread for OAuth"""
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    flask_app.run(port=5000, use_reloader=False, debug=False)


if __name__ == "__main__":
    # Start Flask server for Google OAuth
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start PyQt6 application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window (starts with auth)
    window = KemaslahApp()
    window.show()
    
    sys.exit(app.exec())