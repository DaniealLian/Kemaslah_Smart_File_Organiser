import os
import shutil
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QHeaderView, 
                             QFileIconProvider, QInputDialog, QMessageBox, QAbstractItemView, QMenu)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QFileInfo, QSize

class FileTableWidget(QWidget):
    folder_opened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_path = ""
        self.icon_provider = QFileIconProvider()
        
        # Internal Clipboard
        self.clipboard_files = [] 
        self.clipboard_action = None # 'copy' or 'cut'
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 0, 20, 20)
        
        # Select All Checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setStyleSheet("""
            QCheckBox { color: #C0C0C0; padding: 10px 0; }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #4A5568; border-radius: 4px; background-color: #2D3748;
            }
            QCheckBox::indicator:checked { background-color: #2563EB; border-color: #2563EB; }
        """)
        self.select_all_cb.clicked.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_cb)
        
        # Table Setup
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Date Modified", "Type", "Size"])
        
        # Table Styling & Behavior
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.Shape.NoFrame)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Windows Style Selection
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        self.table.setIconSize(QSize(24, 24))
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: transparent; 
                border: none; 
                color: #E0E0E0;
                selection-background-color: #2563EB;
                selection-color: white;
                outline: 0;
            }
            QHeaderView::section {
                background-color: transparent; 
                color: #888888; 
                border: none;
                padding: 10px; 
                font-weight: bold; 
                text-align: left;
            }
            QTableWidget::item { 
                padding: 8px; 
                border-bottom: 1px solid #2D3748; 
            }
            QTableWidget::item:selected { 
                background-color: #2563EB; 
                color: white;
                border: none;
            }
            QTableWidget::item:selected:!active {
                background-color: #1E40AF; 
                color: white;
            }
            QTableWidget::item:focus {
                border: none;
                outline: none;
            }
        """)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Header Sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Signals
        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.table.itemSelectionChanged.connect(self.update_select_all_state)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_files(self, path):
        self.current_path = path
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.select_all_cb.setChecked(False)
        
        try:
            with os.scandir(path) as entries:
                items = list(entries)
            
            items.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for entry in items:
                if entry.name.startswith('.'): continue
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # 1. Name
                name_item = QTableWidgetItem(entry.name)
                # Store vital data in the item itself
                name_item.setData(Qt.ItemDataRole.UserRole, entry.is_dir())
                name_item.setData(Qt.ItemDataRole.UserRole + 1, entry.path)
                
                file_info = QFileInfo(entry.path)
                name_item.setIcon(self.icon_provider.icon(file_info))
                self.table.setItem(row, 0, name_item)
                
                # 2. Date
                mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                self.table.setItem(row, 1, QTableWidgetItem(mod_time.strftime("%d/%m/%Y")))
                
                # 3. Type
                type_str = "File Folder" if entry.is_dir() else "File"
                if not entry.is_dir() and '.' in entry.name:
                    type_str = entry.name.split('.')[-1].upper() + " File"
                self.table.setItem(row, 2, QTableWidgetItem(type_str))
                
                # 4. Size
                size_str = "-"
                if not entry.is_dir():
                    s = entry.stat().st_size
                    if s > 1024**3: size_str = f"{s/(1024**3):.1f} GB"
                    elif s > 1024**2: size_str = f"{s/(1024**2):.1f} MB"
                    elif s > 1024: size_str = f"{s/1024:.0f} KB"
                    else: size_str = f"{s} B"
                self.table.setItem(row, 3, QTableWidgetItem(size_str))
                
        except PermissionError:
            QMessageBox.warning(self, "Access Denied", "You do not have permission to access this folder.")
            # Go back or stay? For now, we just clear the table
        finally:
            self.table.blockSignals(False)

    # --- FUNCTIONALITY METHODS ---
    
    def toggle_select_all(self):
        if self.select_all_cb.isChecked():
            self.table.selectAll()
        else:
            self.table.clearSelection()

    def update_select_all_state(self):
        # Only check "Select All" if literally every row is selected
        total_rows = self.table.rowCount()
        selected_rows_count = len(self.table.selectionModel().selectedRows())
        
        if total_rows > 0 and selected_rows_count == total_rows:
            self.select_all_cb.setChecked(True)
        else:
            self.select_all_cb.setChecked(False)

    def get_selected_files(self):
        """Robust way to get selected paths using column 0"""
        selected_paths = []
        # Using selectedItems is safer than selectedRows for getting data
        for item in self.table.selectedItems():
            # We only stored the path in Column 0 (Name)
            if item.column() == 0:
                path = item.data(Qt.ItemDataRole.UserRole + 1)
                if path:
                    selected_paths.append(path)
        return selected_paths

    def perform_action(self, action_name):
        selected_files = self.get_selected_files()
        
        # Debug print to verify selection works
        # print(f"Action: {action_name}, Files: {selected_files}")
        
        if action_name == "new":
            self.create_new_folder()
            
        elif action_name == "rename":
            if len(selected_files) != 1:
                QMessageBox.warning(self, "Rename", "Please select exactly one item to rename.")
                return
            self.rename_item(selected_files[0])
            
        elif action_name == "delete":
            if not selected_files: 
                QMessageBox.information(self, "Delete", "No files selected.")
                return
            self.delete_items(selected_files)
            
        elif action_name == "copy":
            if not selected_files: return
            self.clipboard_files = selected_files
            self.clipboard_action = 'copy'
            
        elif action_name == "cut":
            if not selected_files: return
            self.clipboard_files = selected_files
            self.clipboard_action = 'cut'
            
        elif action_name == "paste":
            self.paste_items()
            
        elif action_name == "share":
            pass

    def create_new_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name:
            try:
                path = os.path.join(self.current_path, name)
                os.mkdir(path)
                self.load_files(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder:\n{str(e)}")

    def rename_item(self, old_path):
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=old_name)
        if ok and new_name:
            try:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                self.load_files(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename:\n{str(e)}")

    def delete_items(self, paths):
        text = f"Are you sure you want to delete {len(paths)} items?"
        if len(paths) == 1:
            text = f"Are you sure you want to delete '{os.path.basename(paths[0])}'?"
            
        reply = QMessageBox.question(self, "Delete", text,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            for path in paths:
                try:
                    if os.path.isdir(path):
                        # Force delete directory
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not delete {os.path.basename(path)}:\n{e}")
            self.load_files(self.current_path)

    def paste_items(self):
        if not self.clipboard_files: return
        
        for src_path in self.clipboard_files:
            # Check if source still exists
            if not os.path.exists(src_path):
                continue

            file_name = os.path.basename(src_path)
            dest_path = os.path.join(self.current_path, file_name)
            
            # --- FIX: Handle duplicate names loop (Copy 1, Copy 2, etc.) ---
            base, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(dest_path):
                # If we are "Cutting" and the dest is the same as source, do nothing
                if self.clipboard_action == 'cut' and os.path.samefile(src_path, dest_path):
                    break 
                
                dest_path = os.path.join(self.current_path, f"{base}_copy{counter}{ext}")
                counter += 1
            
            # If after loop we are pointing to same file (Cut operation), skip
            if self.clipboard_action == 'cut' and os.path.exists(dest_path) and os.path.samefile(src_path, dest_path):
                continue

            try:
                if self.clipboard_action == 'copy':
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        shutil.copy2(src_path, dest_path)
                elif self.clipboard_action == 'cut':
                    shutil.move(src_path, dest_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to paste {file_name}\n{str(e)}")
        
        # Clear clipboard if it was a cut operation
        if self.clipboard_action == 'cut':
            self.clipboard_files = []
            self.clipboard_action = None
            
        self.load_files(self.current_path)

    def on_double_click(self, row, col):
        name_item = self.table.item(row, 0)
        is_dir = name_item.data(Qt.ItemDataRole.UserRole)
        full_path = name_item.data(Qt.ItemDataRole.UserRole + 1)
        
        if is_dir:
            self.folder_opened.emit(full_path)
        else:
            try:
                os.startfile(full_path)
            except Exception as e:
                print(f"Error opening file: {e}")
    
    def show_context_menu(self, position):
        # 1. Check if a specific item was clicked
        item = self.table.itemAt(position)
        has_selection = item is not None

        # 2. Create the Menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D3748;
                color: #E0E0E0;
                border: 1px solid #4A5568;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2563EB;
                color: white;
            }
            QMenu::item:disabled {
                color: #718096;
            }
        """)

        # 3. Create Actions matching the ActionBar
        action_new = QAction("➕ New", self)
        action_cut = QAction("✂ Cut", self)
        action_copy = QAction("📋 Copy", self)
        action_paste = QAction("📄 Paste", self)
        action_rename = QAction("✏ Rename", self)
        action_share = QAction("⤴ Share", self)
        action_delete = QAction("🗑 Delete", self)

        # 4. Disable actions that require a file to be selected if clicking empty space
        if not has_selection:
            action_cut.setEnabled(False)
            action_copy.setEnabled(False)
            action_rename.setEnabled(False)
            action_share.setEnabled(False)
            action_delete.setEnabled(False)

        # 5. Disable Paste if clipboard is empty
        if not self.clipboard_files:
            action_paste.setEnabled(False)

        # 6. Add Actions to Menu
        menu.addAction(action_new)
        menu.addSeparator() # Adds a nice visual line
        menu.addAction(action_cut)
        menu.addAction(action_copy)
        menu.addAction(action_paste)
        menu.addSeparator()
        menu.addAction(action_rename)
        menu.addAction(action_share)
        menu.addSeparator()
        menu.addAction(action_delete)

        # 7. Show the menu and capture the user's choice
        action = menu.exec(self.table.viewport().mapToGlobal(position))

        # 8. Route the choice to your existing logic
        if action == action_new: self.perform_action("new")
        elif action == action_cut: self.perform_action("cut")
        elif action == action_copy: self.perform_action("copy")
        elif action == action_paste: self.perform_action("paste")
        elif action == action_rename: self.perform_action("rename")
        elif action == action_share: self.perform_action("share")
        elif action == action_delete: self.perform_action("delete")