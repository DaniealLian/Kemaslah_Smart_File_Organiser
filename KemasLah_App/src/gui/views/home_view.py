import os
import shutil
import datetime
import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QStackedWidget)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal

# Import your custom widgets
from ..widgets.stat_card import StatCard

class HomeView(QWidget):
    # Signal to navigate to All Files page and optionally open a specific path
    navigate_to_path = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.tab_buttons = {} # Store buttons to update styles
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- 1. REAL STORAGE STATS ---
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(20, 20, 20, 10)
        stats_layout.setSpacing(15)
        
        total_gb, used_gb, free_gb = self.get_disk_usage()
        
        total_card = StatCard("Local Disk (C:)", used_gb, total_gb, "#2563EB")
        archive_card = StatCard("Potentially Archivable", 15, 125, "#8B5CF6")
        
        stats_layout.addWidget(total_card, 1)
        stats_layout.addWidget(archive_card, 1)
        layout.addLayout(stats_layout)
        
        # --- 2. TABS (Buttons) ---
        tabs_layout = QVBoxLayout()
        tabs_layout.setContentsMargins(20, 10, 20, 0)
        
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setSpacing(20)
        
        tabs = ["Recent", "Favorites", "Shared"]
        
        for tab_name in tabs:
            btn = QPushButton(tab_name)
            btn.setCheckable(True)
            # Connect click to switch_tab method
            btn.clicked.connect(lambda checked, t=tab_name: self.switch_tab(t))
            
            # Default style (Inactive)
            btn.setStyleSheet(self.get_tab_style(False))
            
            tab_buttons_layout.addWidget(btn)
            self.tab_buttons[tab_name] = btn
        
        # Set "Recent" as active initially
        self.tab_buttons["Recent"].setChecked(True)
        self.tab_buttons["Recent"].setStyleSheet(self.get_tab_style(True))
        
        tab_buttons_layout.addStretch()
        tabs_layout.addLayout(tab_buttons_layout)
        
        # --- 3. CONTENT STACK (Tables) ---
        self.content_stack = QStackedWidget()
        
        # Create the 3 tables
        self.recent_table = self.create_file_table(self.get_windows_recent_files())
        self.favorites_table = self.create_file_table(self.get_favorites_files())
        self.shared_table = self.create_file_table(self.get_shared_files())
        
        # Add to stack in order: 0=Recent, 1=Favorites, 2=Shared
        self.content_stack.addWidget(self.recent_table)
        self.content_stack.addWidget(self.favorites_table)
        self.content_stack.addWidget(self.shared_table)
        
        tabs_layout.addWidget(self.content_stack)
        layout.addLayout(tabs_layout)
        self.setLayout(layout)

    # --- TAB LOGIC ---
    def switch_tab(self, tab_name):
        # 1. Update Buttons Visuals
        for name, btn in self.tab_buttons.items():
            is_active = (name == tab_name)
            btn.setChecked(is_active)
            btn.setStyleSheet(self.get_tab_style(is_active))
        
        # 2. Switch Stack Content
        if tab_name == "Recent":
            self.content_stack.setCurrentIndex(0)
        elif tab_name == "Favorites":
            self.content_stack.setCurrentIndex(1)
        elif tab_name == "Shared":
            self.content_stack.setCurrentIndex(2)

    def get_tab_style(self, active):
        if active:
            return """
                QPushButton {
                    padding: 10px 20px;
                    background-color: transparent;
                    color: #2563EB;
                    border: none;
                    border-bottom: 2px solid #2563EB;
                    font-weight: bold;
                }
            """
        else:
            return """
                QPushButton {
                    padding: 10px 20px;
                    background-color: transparent;
                    color: #888888;
                    border: none;
                    border-bottom: 2px solid transparent;
                    font-weight: bold;
                }
                QPushButton:hover { color: #C0C0C0; }
            """

    # --- DATA FETCHING ---
    def get_disk_usage(self):
        try:
            total, used, free = shutil.disk_usage(os.path.abspath(os.sep))
            return (total // (2**30), used // (2**30), free // (2**30))
        except:
            return (500, 250, 250)

    def resolve_shortcut(self, lnk_path):
        """Resolve a .lnk shortcut to its target using PowerShell"""
        try:
            # Use PowerShell to resolve the shortcut
            ps_command = f'(New-Object -ComObject WScript.Shell).CreateShortcut("{lnk_path}").TargetPath'
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW  # Don't show PowerShell window
            )
            
            if result.returncode == 0:
                target_path = result.stdout.strip()
                if target_path and os.path.exists(target_path):
                    return target_path
        except Exception as e:
            print(f"Failed to resolve shortcut: {e}")
        
        return None

    def get_windows_recent_files(self):
        # Scans %APPDATA%/Microsoft/Windows/Recent
        path = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Recent')
        return self.scan_folder_for_table(path, limit=15)

    def get_favorites_files(self):
        # Scans %UserProfile%/Links (Quick Access) or Favorites
        path = os.path.expanduser(r'~\Links')
        if not os.path.exists(path):
            path = os.path.expanduser(r'~\Favorites')
        return self.scan_folder_for_table(path)

    def get_shared_files(self):
        # Scans C:/Users/Public/Documents
        # Place holder can delete when the actual share feature is implemented 
        path = r'C:\Users\Public\Documents'
        return self.scan_folder_for_table(path)

    def scan_folder_for_table(self, folder_path, limit=None):
        files_data = []
        if not os.path.exists(folder_path):
            return []

        try:
            with os.scandir(folder_path) as entries:
                # Sort by Date Modified (Newest first)
                sorted_entries = sorted(
                    [e for e in entries if e.is_file()],
                    key=lambda e: e.stat().st_mtime,
                    reverse=True
                )
                
            if limit:
                sorted_entries = sorted_entries[:limit]

            for entry in sorted_entries:
                name = entry.name
                # Remove .lnk extension for display
                if name.lower().endswith('.lnk'):
                    name = name[:-4]
                
                # Filter out system files
                if name.lower() in ["desktop.ini", "thumbs.db"]: continue

                dt = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                date_str = dt.strftime("%d/%m %H:%M")
                
                ext = "File"
                if '.' in name:
                    ext = name.split('.')[-1].upper()
                
                # Store both display name and full path
                # Also determine if this is a directory (for .lnk shortcuts, we need to resolve)
                is_folder = entry.is_dir()
                target_path = entry.path
                
                # Try to resolve .lnk shortcuts to get the actual target
                if entry.name.lower().endswith('.lnk'):
                    resolved_path = self.resolve_shortcut(entry.path)
                    if resolved_path:
                        target_path = resolved_path
                        is_folder = os.path.isdir(target_path)
                        print(f"DEBUG: Resolved '{name}' -> '{target_path}', is_folder={is_folder}")
                    else:
                        print(f"DEBUG: Could not resolve '{name}'")
                
                files_data.append((name, date_str, ext, target_path, is_folder))
                
        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")
            
        return files_data

    # --- TABLE CREATION ---
    def create_file_table(self, data):
        table = QTableWidget()
        columns = ["File Name", "Date Modified", "Type"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(data))
        
        # Styling
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setFrameShape(QTableWidget.Shape.NoFrame)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; color: #E0E0E0; }
            QHeaderView::section {
                background-color: transparent; color: #888888; border: none;
                padding: 10px; font-weight: bold; text-align: left;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #2D3748; }
            QTableWidget::item:selected { background-color: #2563EB; color: white; }
            QTableWidget::item:focus { outline: none; }
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(2, 100)

        for row, (name, date_str, file_type, full_path, is_folder) in enumerate(data):
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, full_path)
            item_name.setData(Qt.ItemDataRole.UserRole + 1, is_folder)  # Store if it's a folder
            item_name.setForeground(QColor("white"))
            table.setItem(row, 0, item_name)
            
            item_date = QTableWidgetItem(date_str)
            item_date.setForeground(QColor("#aaaaaa"))
            table.setItem(row, 1, item_date)
            
            item_type = QTableWidgetItem(file_type)
            item_type.setForeground(QColor("#888888"))
            table.setItem(row, 2, item_type)
            
        # Connect Double Click
        table.cellDoubleClicked.connect(self.open_item)
        return table

    def open_item(self, row, col):
        # Determine which table sent the signal
        sender = self.sender() 
        if not sender: 
            print("DEBUG: No sender!")
            return
        
        item = sender.item(row, 0)
        path = item.data(Qt.ItemDataRole.UserRole)
        is_folder = item.data(Qt.ItemDataRole.UserRole + 1)
        
        print(f"DEBUG: open_item called - path='{path}', is_folder={is_folder}")
        
        if path and os.path.exists(path):
            if is_folder:
                # Navigate to All Files page with this folder
                print(f"DEBUG: Emitting navigate_to_path signal with path: {path}")
                self.navigate_to_path.emit(path)
            else:
                # For files, open them with the default application
                print(f"DEBUG: Opening file with os.startfile: {path}")
                try:
                    os.startfile(path)
                except Exception as e:
                    print(f"Could not open file: {e}")
        else:
            print(f"DEBUG: Path doesn't exist or is None: {path}")