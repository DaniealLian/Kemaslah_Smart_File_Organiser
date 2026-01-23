import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

# Keep your other widgets
from ..widgets.stat_card import StatCard

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 2. Stats Cards
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(20, 20, 20, 10)
        stats_layout.setSpacing(15)
        
        total_card = StatCard("Total File Size", 20, 125, "#2563EB")
        archive_card = StatCard("Potentially Archivable Files", 20, 125, "#2563EB")
        
        stats_layout.addWidget(total_card, 1)
        stats_layout.addWidget(archive_card, 1)
        layout.addLayout(stats_layout)
        
        # 3. Tabs (Visual Only for now)
        tabs_layout = QVBoxLayout()
        tabs_layout.setContentsMargins(20, 10, 20, 0)
        
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setSpacing(20)
        
        for tab_name in ["Recent", "Favorites", "Shared"]:
            tab_btn = QPushButton(tab_name)
            tab_btn.setCheckable(True)
            if tab_name == "Recent":
                tab_btn.setChecked(True)
            tab_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px;
                    background-color: transparent;
                    color: #888888;
                    border: none;
                    border-bottom: 2px solid transparent;
                    font-weight: bold;
                }
                QPushButton:checked {
                    color: #2563EB;
                    border-bottom: 2px solid #2563EB;
                }
                QPushButton:hover {
                    color: #C0C0C0;
                }
            """)
            tab_buttons_layout.addWidget(tab_btn)
        
        tab_buttons_layout.addStretch()
        tabs_layout.addLayout(tab_buttons_layout)
        
        # 4. RECENT FILES TABLE (Custom Implementation)
        self.recent_table = self.create_recent_table()
        tabs_layout.addWidget(self.recent_table)
        
        layout.addLayout(tabs_layout)
        self.setLayout(layout)

    def create_recent_table(self):
        """Builds a specific table just for showing recent file history"""
        table = QTableWidget()
        
        # Define Columns
        columns = ["File Name", "Date Accessed", "File Location"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Fetch Data (Currently Dummy, later connect to DB)
        recent_data = self.get_recent_files()
        table.setRowCount(len(recent_data))
        
        # Styling
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setFrameShape(QTableWidget.Shape.NoFrame)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #E0E0E0;
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
                padding: 10px;
                border-bottom: 1px solid #2D3748;
            }
            QTableWidget::item:selected {
                background-color: #2C5282;
            }
        """)
        
        # Header Resizing
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Populate Rows
        for row, (name, date, location) in enumerate(recent_data):
            # Name
            item_name = QTableWidgetItem(name)
            item_name.setForeground(QColor("white"))
            table.setItem(row, 0, item_name)
            
            # Date
            item_date = QTableWidgetItem(date)
            item_date.setForeground(QColor("#aaaaaa"))
            table.setItem(row, 1, item_date)
            
            # Location
            item_loc = QTableWidgetItem(location)
            item_loc.setForeground(QColor("#888888"))
            table.setItem(row, 2, item_loc)
            
        return table

    def get_recent_files(self):
        """
        Returns the list of recently accessed files.
        TODO: Connect this to a real database or log file later.
        """
        return [
            ("Research_Paper.pdf", "10/12/2025", "C:/Users/User/Documents"),
            ("Budget_2025.xlsx", "08/11/2025", "C:/Users/User/Documents/Finance"),
            ("Demo_Video.mp4", "07/11/2025", "C:/Users/User/Videos"),
            ("Profile_Pic.jpg", "05/09/2025", "C:/Users/User/Pictures"),
            ("Notes.txt", "01/09/2025", "C:/Users/User/Desktop")
        ]