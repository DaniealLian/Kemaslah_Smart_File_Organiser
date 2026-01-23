from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

class HomePage(QWidget):
    def __init__(self, navigation_callback):
        super().__init__()
        self.nav_callback = navigation_callback # Function to switch tabs
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # --- 1. TOP HEADER (Welcome + Search) ---
        header_layout = QHBoxLayout()
        
        welcome_text = QLabel("Welcome back, Danieal")
        welcome_text.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search your files...")
        self.search_bar.setFixedWidth(400)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #cccccc;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #3e3e3e;
                font-size: 14px;
            }
        """)

        header_layout.addWidget(welcome_text)
        header_layout.addStretch()
        header_layout.addWidget(self.search_bar)
        
        self.layout.addLayout(header_layout)

        # --- 2. STATISTICS CARDS (Visual Dashboard) ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # Card 1: Storage
        self.card_storage = self.create_stat_card("💾 Storage Used", "45% Used", "120 GB Free", "#0078D4")
        # Card 2: Files Sorted
        self.card_sorted = self.create_stat_card("⚡ Files Sorted", "1,240", "Last 7 Days", "#107C10")
        # Card 3: Archivable
        self.card_archive = self.create_stat_card("📦 Ready to Archive", "185 Files", "Savings: 2.4GB", "#D83B01")

        stats_layout.addWidget(self.card_storage)
        stats_layout.addWidget(self.card_sorted)
        stats_layout.addWidget(self.card_archive)
        
        self.layout.addLayout(stats_layout)

        # --- 3. CORE FEATURES (Quick Access) ---
        section_title = QLabel("Quick Actions")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cccccc; margin-top: 10px;")
        self.layout.addWidget(section_title)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)

        # Smart Sort Button (Big Feature)
        self.btn_smart_sort = self.create_action_card("🧠 Smart Organise", "Scan & Sort Folder", 1)
        # Auto Archive Button (Big Feature)
        self.btn_auto_archive = self.create_action_card("📦 Auto Archive", "Clean up old files", 2)
        
        actions_layout.addWidget(self.btn_smart_sort)
        actions_layout.addWidget(self.btn_auto_archive)
        
        self.layout.addLayout(actions_layout)

        # --- 4. RECENT FILES TABLE (Explorer Style) ---
        recent_title = QLabel("Recent Activity")
        recent_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cccccc; margin-top: 10px;")
        self.layout.addWidget(recent_title)

        self.recent_table = self.create_recent_table()
        self.layout.addWidget(self.recent_table)

    def create_stat_card(self, title, value, subtext, accent_color):
        """Creates a small stat box similar to Windows 11 Widgets"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2b2b2b;
                border-radius: 10px;
                border-left: 5px solid {accent_color};
            }}
        """)
        card.setFixedHeight(100)
        layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #aaaaaa; font-size: 12px; font-weight: bold;")
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        
        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet("color: #888888; font-size: 11px;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_sub)
        return card

    def create_action_card(self, title, desc, target_index):
        """Creates a clickable card that navigates to other tabs"""
        btn = QPushButton()
        btn.setFixedHeight(80)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.nav_callback(target_index)) # Navigates when clicked
        
        # We use a layout inside the button to make it look like a card
        layout = QVBoxLayout(btn)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("font-size: 12px; color: #aaaaaa; background: transparent;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 8px;
                text-align: left;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3e3e3e;
                border: 1px solid #555555;
            }
        """)
        return btn

    def create_recent_table(self):
        """Creates a file list similar to Windows Explorer"""
        table = QTableWidget(4, 3) # 4 Rows, 3 Cols
        table.setHorizontalHeaderLabels(["Name", "Date Modified", "Type"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: none;
                color: white;
                gridline-color: #3e3e3e;
            }
            QHeaderView::section {
                background-color: #202020;
                color: #aaaaaa;
                padding: 5px;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        # Dummy Data (Replace with real logs later)
        data = [
            ("Project_Report.docx", "Oct 24, 2024", "Document"),
            ("Family_Trip.jpg", "Oct 23, 2024", "Image"),
            ("Invoice_001.pdf", "Oct 23, 2024", "Document"),
            ("Setup.exe", "Oct 22, 2024", "Application")
        ]
        
        for row, (name, date, type_) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(date))
            table.setItem(row, 2, QTableWidgetItem(type_))
            
        return table