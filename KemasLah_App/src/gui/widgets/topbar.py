import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import pyqtSignal, QDir

class TopBar(QWidget):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        self.breadcrumb_layout = QHBoxLayout()
        self.breadcrumb_layout.setSpacing(5)
        
        # Search bar setup...
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
        self.current_path = path
        
        # 1. Clear old buttons
        while self.breadcrumb_layout.count():
            child = self.breadcrumb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Handle Special Pages (Home, Settings, etc.)
        if path in ["Home", "Smart Archive", "Settings", "Statistics"] or not os.path.isabs(path):
            self.add_crumb_label(path)
            return

        # 3. Handle Real File Paths (e.g., C:/Users/Docs)
        path = os.path.normpath(path)
        parts = path.split(os.sep)
        
        # Filter out empty parts
        parts = [p for p in parts if p]
        
        # Smart truncation: Show only last 3 segments if path is too long
        MAX_SEGMENTS = 3
        show_ellipsis = len(parts) > MAX_SEGMENTS
        
        if show_ellipsis:
            # Keep the first part (drive) and last 2 parts
            visible_parts = [parts[0]] + parts[-(MAX_SEGMENTS-1):]
            full_parts = parts  # Keep full path for building correct paths
        else:
            visible_parts = parts
            full_parts = parts
        
        current_build_path = ""
        
        for i, part in enumerate(full_parts):
            # Windows drive fix (e.g., "C:") needs a slash to be valid
            if i == 0 and ':' in part:
                current_build_path = part + os.sep
            else:
                current_build_path = os.path.join(current_build_path, part)
            
            # Only show certain breadcrumbs based on truncation
            should_show = False
            
            if show_ellipsis:
                # Show first segment (drive)
                if i == 0:
                    should_show = True
                # Show ellipsis after drive
                elif i == 1:
                    self.add_ellipsis()
                # Show last (MAX_SEGMENTS - 1) segments
                elif i >= len(full_parts) - (MAX_SEGMENTS - 1):
                    should_show = True
            else:
                # Show all segments if not truncated
                should_show = True
            
            if should_show:
                # Add Button
                self.add_crumb_button(part, current_build_path)
                
                # Add Separator ">" (except for the last item)
                if i < len(full_parts) - 1:
                    sep = QLabel(">")
                    sep.setStyleSheet("color: #666666; font-weight: bold;")
                    self.breadcrumb_layout.addWidget(sep)

    def add_crumb_button(self, text, full_path):
        btn = QPushButton(text)
        # Store the path properly so the lambda captures the specific path for this button
        btn.clicked.connect(lambda checked, p=full_path: self.path_changed.emit(p))
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #C0C0C0;
                border: none;
                font-weight: bold;
                padding: 2px 5px;
            }
            QPushButton:hover {
                color: #4A9EFF;
                background-color: #2D3748;
                border-radius: 4px;
            }
        """)
        self.breadcrumb_layout.addWidget(btn)

    def add_crumb_label(self, text):
        """Used for static pages like Home where you can't click back"""
        label = QLabel(text)
        label.setStyleSheet("color: #C0C0C0; font-weight: bold; font-size: 14px; padding-left: 5px;")
        self.breadcrumb_layout.addWidget(label)
    
    def add_ellipsis(self):
        """Add an ellipsis (...) to indicate hidden path segments"""
        ellipsis = QLabel("...")
        ellipsis.setStyleSheet("color: #666666; font-weight: bold; padding: 0 5px;")
        self.breadcrumb_layout.addWidget(ellipsis)