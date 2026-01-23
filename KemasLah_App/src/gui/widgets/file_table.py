import os
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QHeaderView, QApplication)
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal

class FileTableWidget(QWidget):
    # Signal: Emitted when a folder is double-clicked
    folder_opened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_path = ""
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 0, 20, 20)
        
        # Select All
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setStyleSheet("""
            QCheckBox { color: #C0C0C0; padding: 10px 0; }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #4A5568; border-radius: 4px; background-color: #2D3748;
            }
            QCheckBox::indicator:checked { background-color: #2563EB; border-color: #2563EB; }
        """)
        layout.addWidget(self.select_all_cb)
        
        # Table Setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Name", "Date Modified", "Type", "Size"])
        
        # Style
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.Shape.NoFrame)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; color: #E0E0E0; }
            QHeaderView::section {
                background-color: transparent; color: #888888; border: none;
                padding: 10px; font-weight: bold; text-align: left;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #2D3748; }
            QTableWidget::item:selected { background-color: #2C5282; }
        """)
        
        # Header sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed) # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name
        self.table.setColumnWidth(0, 50)
        
        # Double Click Action
        self.table.cellDoubleClicked.connect(self.on_double_click)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_files(self, path):
        """Reads real files from disk and puts them in the table"""
        self.current_path = path
        self.table.setRowCount(0) # Clear table
        
        try:
            # Get all items in directory
            with os.scandir(path) as entries:
                items = list(entries)
                
            # Filter: Sort by Folders first, then Files
            items.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for entry in items:
                # Skip hidden files
                if entry.name.startswith('.'): continue
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # 1. Checkbox Widget
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setContentsMargins(10, 0, 0, 0)
                checkbox = QCheckBox()
                checkbox.setStyleSheet("""
                    QCheckBox::indicator {
                        width: 16px; height: 16px; border: 2px solid #4A5568;
                        border-radius: 3px; background-color: #2D3748;
                    }
                    QCheckBox::indicator:checked { background-color: #2563EB; border-color: #2563EB; }
                """)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.addStretch()
                self.table.setCellWidget(row, 0, checkbox_widget)
                
                # 2. File Details
                # Name
                name_item = QTableWidgetItem(entry.name)
                # Store whether it's a folder for sorting/logic
                name_item.setData(Qt.ItemDataRole.UserRole, entry.is_dir())
                
                # Date
                mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                date_str = mod_time.strftime("%d/%m/%Y")
                
                # Type
                type_str = "File Folder" if entry.is_dir() else "File"
                if not entry.is_dir() and '.' in entry.name:
                    type_str = entry.name.split('.')[-1].upper() + " File"
                    
                # Size
                size_str = "-"
                if not entry.is_dir():
                    size_bytes = entry.stat().st_size
                    if size_bytes > 1024*1024*1024: size_str = f"{size_bytes/(1024**3):.1f} GB"
                    elif size_bytes > 1024*1024: size_str = f"{size_bytes/(1024**2):.1f} MB"
                    elif size_bytes > 1024: size_str = f"{size_bytes/1024:.0f} KB"
                    else: size_str = f"{size_bytes} B"

                self.table.setItem(row, 1, name_item)
                self.table.setItem(row, 2, QTableWidgetItem(date_str))
                self.table.setItem(row, 3, QTableWidgetItem(type_str))
                self.table.setItem(row, 4, QTableWidgetItem(size_str))
                
        except PermissionError:
            pass # Handle access denied folders gracefully

    def on_double_click(self, row, col):
        """Handle navigation"""
        name_item = self.table.item(row, 1)
        is_dir = name_item.data(Qt.ItemDataRole.UserRole)
        file_name = name_item.text()
        full_path = os.path.join(self.current_path, file_name)
        
        if is_dir:
            self.folder_opened.emit(full_path)
        else:
            os.startfile(full_path)
            
    def load_manual_data(self, columns, data):
        """Allows manually populating the table (for Archive/Dummy views)"""
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            # Checkbox column
            checkbox_widget = QWidget()
            cb_layout = QHBoxLayout(checkbox_widget)
            cb_layout.setContentsMargins(10,0,0,0)
            cb_layout.addWidget(QCheckBox())
            self.table.setCellWidget(row_idx, 0, checkbox_widget)
            
            # Data columns
            # Note: Adjust indices based on your data structure
            # If your data tuple is (Name, Date, Type, Size), mapping starts at col 1
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx + 1, QTableWidgetItem(str(value)))