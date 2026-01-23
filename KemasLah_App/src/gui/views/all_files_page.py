import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
                             QLineEdit, QPushButton, QHeaderView, QAbstractItemView)
# QFileSystemModel is in QtGui for PyQt6
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir, Qt

class AllFilesPage(QWidget):
    def __init__(self):
        super().__init__()

        # Define the Sandbox Root (User's Home Directory)
        self.home_path = QDir.toNativeSeparators(QDir.homePath())

        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # --- 1. TOP NAVIGATION BAR ---
        nav_layout = QHBoxLayout()

        self.btn_up = QPushButton("⬆ Up")
        self.btn_up.setFixedWidth(80)
        self.btn_up.clicked.connect(self.go_up_directory)
        # Default style for enabled/disabled states
        self.btn_up.setStyleSheet("""
            QPushButton {
                background-color: #333; color: white; border: 1px solid #555;
                padding: 6px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:disabled { background-color: #222; color: #555; border: 1px solid #333; }
        """)

        self.address_bar = QLineEdit()
        self.address_bar.setReadOnly(True)
        self.address_bar.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b; color: #aaa; border: 1px solid #3e3e3e;
                padding: 6px; border-radius: 4px;
            }
        """)

        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.address_bar)
        self.layout.addLayout(nav_layout)

        # --- 2. FILE SYSTEM MODEL ---
        self.model = QFileSystemModel()
        # Filter: Show Dirs & Files, No Hidden, No "Dot" folders
        # self.model.setFilter(QDir.Filter.Dirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        
        # Crucial: setRootPath must be called for the model to load this part of the drive
        self.model.setRootPath(self.home_path)

        # --- 3. TREE VIEW ---
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        
        # Set the VIEW to start exactly at the Home Path
        self.tree_view.setRootIndex(self.model.index(self.home_path))
        
        # Styling
        self.tree_view.setAlternatingRowColors(False)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #1e1e1e; color: #ffffff;
                border: 1px solid #333; border-radius: 6px; font-size: 14px;
            }
            QTreeView::item { padding: 6px; }
            QTreeView::item:hover { background-color: #2d2d2d; }
            QTreeView::item:selected { background-color: #0078D4; color: white; }
            QHeaderView::section {
                background-color: #2b2b2b; color: #cccccc;
                padding: 8px; border: none; border-bottom: 1px solid #444;
            }
        """)

        # Column Config
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_view.setColumnWidth(0, 300)

        # Connect Double Click
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # Initial State Check
        self.update_navigation_state(self.home_path)
        
        self.layout.addWidget(self.tree_view)

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.tree_view.setRootIndex(index)
            self.update_navigation_state(path)
        else:
            os.startfile(path)

    def go_up_directory(self):
        current_index = self.tree_view.rootIndex()
        current_path = QDir.toNativeSeparators(self.model.filePath(current_index))
        
        # SECURITY CHECK: If we are already at Home, STOP.
        if current_path == self.home_path:
            return

        parent_path = os.path.dirname(current_path)
        
        # Double check: Ensure the parent is still inside/equal to home path
        # (This handles weird edge cases, though the == check above usually catches it)
        if self.home_path in parent_path or parent_path == self.home_path:
            new_index = self.model.index(parent_path)
            self.tree_view.setRootIndex(new_index)
            self.update_navigation_state(parent_path)

    def update_navigation_state(self, path):
        """Updates Address Bar and Disables 'Up' button if at root"""
        clean_path = QDir.toNativeSeparators(path)
        self.address_bar.setText(clean_path)
        
        # Disable "Up" button if we are at the sandbox limit
        if clean_path == self.home_path:
            self.btn_up.setEnabled(False)
        else:
            self.btn_up.setEnabled(True)