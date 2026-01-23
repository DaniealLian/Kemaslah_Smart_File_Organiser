import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QListWidget, 
                             QListWidgetItem, QCheckBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QStackedWidget,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCharts import QChart, QChartView, QPieSeries


class CircularImage(QLabel):
    """Custom widget for circular profile image"""
    def __init__(self, size=50):
        super().__init__()
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #4A9EFF;
                border-radius: {size//2}px;
            }}
        """)


class Sidebar(QWidget):
    """Left sidebar navigation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)
        
        # Profile section
        profile_widget = QWidget()
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(20, 10, 20, 20)
        
        profile_pic = CircularImage(40)
        profile_layout.addWidget(profile_pic)
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        title_label = QLabel("Title")
        title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("color: #888888; font-size: 11px;")
        profile_info.addWidget(title_label)
        profile_info.addWidget(desc_label)
        profile_layout.addLayout(profile_info)
        
        # Sign out icon
        signout_btn = QPushButton("→")
        signout_btn.setFixedSize(30, 30)
        signout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF4444;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.1);
            }
        """)
        profile_layout.addWidget(signout_btn)
        
        profile_widget.setLayout(profile_layout)
        layout.addWidget(profile_widget)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("Home", "home"),
            ("All Files", "files"),
            ("Documents", "documents"),
            ("Auto Archive", "archive"),
            ("File Sharing", "sharing"),
            ("Statistics", "statistics"),
            ("Settings", "settings")
        ]
        
        for text, identifier in nav_items:
            btn = QPushButton(text)
            btn.setProperty("identifier", identifier)
            btn.setCheckable(True)
            is_submenu = text.startswith("  ")
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 20px;
                    padding-left: {'40px' if is_submenu else '20px'};
                    border: none;
                    background-color: transparent;
                    color: #C0C0C0;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #3A3A4A;
                    color: #FFFFFF;
                }}
                QPushButton:checked {{
                    background-color: #4A5568;
                    color: #FFFFFF;
                }}
            """)
            
            btn.clicked.connect(lambda checked, b=btn: self.on_nav_clicked(b))
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Set home as default
        self.nav_buttons[0].setChecked(True)
    
    def on_nav_clicked(self, button):
        for btn in self.nav_buttons:
            if btn != button:
                btn.setChecked(False)


class TopBar(QWidget):
    """Top navigation bar with breadcrumbs and search"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Breadcrumb navigation
        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setSpacing(10)
        
        home_btn = QPushButton("🏠")
        home_btn.setStyleSheet(self.get_breadcrumb_style())
        breadcrumb_layout.addWidget(home_btn)
        
        for i in range(3):
            sep = QLabel(">")
            sep.setStyleSheet("color: #888888;")
            breadcrumb_layout.addWidget(sep)
            
            link_btn = QPushButton("⭐ Link")
            link_btn.setStyleSheet(self.get_breadcrumb_style())
            breadcrumb_layout.addWidget(link_btn)
        
        breadcrumb_layout.addStretch()
        layout.addLayout(breadcrumb_layout)
        
        # Search bar
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
            QLineEdit:focus {
                border-color: #4A9EFF;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        search_widget.setLayout(search_layout)
        
        layout.addWidget(search_widget)
        self.setLayout(layout)
    
    def get_breadcrumb_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #C0C0C0;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """


class ActionBar(QWidget):
    """Action buttons bar"""
    def __init__(self, show_smart_button=True, button_text="Smart Organise"):
        super().__init__()
        self.init_ui(show_smart_button, button_text)
        
    def init_ui(self, show_smart_button, button_text):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Action buttons
        actions = [
            ("➕ New", False),
            ("✂ Cut", False),
            ("📋 Copy", False),
            ("📄 Paste", False),
            ("✏ Rename", False),
            ("⤴ Share", False),
            ("🗑 Delete", False)
        ]
        
        for text, _ in actions:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    background-color: #2D3748;
                    color: #E0E0E0;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3A4556;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Smart Organise/Archive button
        if show_smart_button:
            smart_btn = QPushButton(f"✏ {button_text}")
            smart_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px;
                    background-color: #2563EB;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1E40AF;
                }
            """)
            layout.addWidget(smart_btn)
        
        self.setLayout(layout)


class FileTableWidget(QWidget):
    """File listing table"""
    def __init__(self, columns, data):
        super().__init__()
        self.init_ui(columns, data)
        
    def init_ui(self, columns, data):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 0, 20, 20)
        
        # Select All checkbox
        select_all_cb = QCheckBox("Select All")
        select_all_cb.setStyleSheet("""
            QCheckBox {
                color: #C0C0C0;
                padding: 10px 0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4A5568;
                border-radius: 4px;
                background-color: #2D3748;
            }
            QCheckBox::indicator:checked {
                background-color: #2563EB;
                border-color: #2563EB;
            }
        """)
        layout.addWidget(select_all_cb)
        
        # Table
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(columns)
        
        # Style table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1A202C;
                border: none;
                gridline-color: #2D3748;
                color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #2D3748;
            }
            QTableWidget::item:selected {
                background-color: #2C5282;
            }
            QHeaderView::section {
                background-color: #1A202C;
                color: #888888;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #2D3748;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Populate table
        for row, row_data in enumerate(data):
            # Checkbox column
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout()
            checkbox_layout.setContentsMargins(10, 0, 0, 0)
            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #4A5568;
                    border-radius: 3px;
                    background-color: #2D3748;
                }
                QCheckBox::indicator:checked {
                    background-color: #2563EB;
                    border-color: #2563EB;
                }
            """)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            checkbox_widget.setLayout(checkbox_layout)
            table.setCellWidget(row, 0, checkbox_widget)
            
            # Data columns
            for col, value in enumerate(row_data, 1):
                item = QTableWidgetItem(str(value))
                table.setItem(row, col, item)
            
            # Highlight selected row
            if row == 1:  # Second row selected (Videos)
                for col in range(table.columnCount()):
                    if col == 0:
                        checkbox_widget.findChild(QCheckBox).setChecked(True)
                    else:
                        table.item(row, col).setBackground(QColor(44, 82, 130))
        
        layout.addWidget(table)
        self.setLayout(layout)


class StatCard(QWidget):
    """Statistics card widget"""
    def __init__(self, title, value, total, color="#2563EB"):
        super().__init__()
        self.init_ui(title, value, total, color)
        
    def init_ui(self, title, value, total, color):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #C0C0C0; font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Progress bar
        progress_widget = QWidget()
        progress_widget.setFixedHeight(8)
        progress_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #2D3748;
                border-radius: 4px;
            }}
        """)
        
        progress_fill = QWidget(progress_widget)
        progress_width = int((value / total) * progress_widget.width()) if total > 0 else 0
        progress_fill.setGeometry(0, 0, progress_width, 8)
        progress_fill.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(progress_widget)
        
        # Value labels
        value_layout = QHBoxLayout()
        value_label = QLabel(f"{value}GB used")
        value_label.setStyleSheet("color: #E0E0E0; font-size: 12px;")
        total_label = QLabel(f"{total}GB")
        total_label.setStyleSheet("color: #888888; font-size: 12px;")
        
        value_layout.addWidget(value_label)
        value_layout.addStretch()
        value_layout.addWidget(total_label)
        layout.addLayout(value_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            StatCard {
                background-color: #2D3748;
                border-radius: 8px;
            }
        """)


class PieChartWidget(QWidget):
    """Pie chart for file distribution"""
    def __init__(self, title, data):
        super().__init__()
        self.init_ui(title, data)
        
    def init_ui(self, title, data):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create pie chart
        series = QPieSeries()
        colors = ["#D946EF", "#06B6D4", "#22D3EE", "#8B5CF6"]
        
        for i, (label, value) in enumerate(data):
            slice = series.append(label, value)
            slice.setColor(QColor(colors[i % len(colors)]))
            slice.setLabelVisible(True)
            slice.setLabel(f"{int(value)}%")
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#2D3748"))
        chart.legend().setVisible(False)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background-color: transparent; border: none;")
        
        layout.addWidget(chart_view)
        
        # Legend
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(8)
        
        for i, (label, _) in enumerate(data):
            legend_item = QHBoxLayout()
            
            color_box = QLabel()
            color_box.setFixedSize(12, 12)
            color_box.setStyleSheet(f"background-color: {colors[i % len(colors)]}; border-radius: 2px;")
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #C0C0C0; font-size: 11px;")
            
            legend_item.addWidget(color_box)
            legend_item.addWidget(label_widget)
            legend_item.addStretch()
            
            legend_layout.addLayout(legend_item)
        
        layout.addLayout(legend_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            PieChartWidget {
                background-color: #2D3748;
                border-radius: 8px;
            }
        """)


class SmartFileManager(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Smart File Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = Sidebar()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("background-color: #1A202C;")
        
        # Connect navigation
        for btn in sidebar.nav_buttons:
            btn.clicked.connect(self.switch_view)
        
        main_layout.addWidget(sidebar)
        
        # Right content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #1A202C;")
        
        # Create different views
        self.create_file_browser_view()
        self.create_archive_view()
        self.create_home_view()
        self.create_statistics_view()
        
        main_layout.addWidget(self.content_stack)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Set default view
        self.content_stack.setCurrentIndex(2)  # Home view
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A202C;
            }
        """)
    
    def switch_view(self):
        sender = self.sender()
        identifier = sender.property("identifier")
        
        view_map = {
            "home": 2,
            "files": 0,
            "archive": 1,
            "statistics": 3
        }
        
        if identifier in view_map:
            self.content_stack.setCurrentIndex(view_map[identifier])
    
    def create_file_browser_view(self):
        """All Files view (Image 1)"""
        view = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(TopBar())
        layout.addWidget(ActionBar(True, "Smart Organise"))
        
        columns = ["", "Folder Name", "Date Modified", "Type", "Size"]
        data = [
            ("Documents", "12/12/2025", "File Folder", "1 BG"),
            ("Videos", "05/11/2025", "File Folder", "5 BG"),
            ("Images", "01/04/2025", "File Folder", "600 MB"),
            ("Downloads", "04/10/2025", "File Folder", "800 MB"),
            ("Music", "16/09/2024", "File Folder", "100 MB")
        ]
        
        layout.addWidget(FileTableWidget(columns, data))
        
        view.setLayout(layout)
        self.content_stack.addWidget(view)
    
    def create_archive_view(self):
        """Auto Archive view (Image 2)"""
        view = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(TopBar())
        layout.addWidget(ActionBar(True, "Smart Archive"))
        
        # Label checkbox
        label_widget = QWidget()
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(20, 10, 20, 0)
        label_cb = QCheckBox("Label")
        label_cb.setStyleSheet("""
            QCheckBox {
                color: #C0C0C0;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4A5568;
                border-radius: 4px;
                background-color: #2D3748;
            }
        """)
        label_layout.addWidget(label_cb)
        label_layout.addStretch()
        label_widget.setLayout(label_layout)
        layout.addWidget(label_widget)
        
        columns = ["", "Archive Name", "Date Archived", "Type", "Size"]
        data = [
            ("Archive_10/07/2020", "10/07/2020", ".zip", "100MB"),
            ("Archive_25/11/2018", "25/11/2018", ".zip", "200MB"),
            ("Archive_30/12/2010", "30/12/2010", ".zip", "50MB"),
            ("Archive_12/08/2009", "12/08/2009", ".zip", "1GB")
        ]
        
        layout.addWidget(FileTableWidget(columns, data))
        
        view.setLayout(layout)
        self.content_stack.addWidget(view)
    
    def create_home_view(self):
        """Home dashboard view (Image 4)"""
        view = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(TopBar())
        layout.addWidget(ActionBar(True, "Smart Organise"))
        
        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(20, 20, 20, 10)
        stats_layout.setSpacing(15)
        
        total_card = StatCard("Total File Size", 20, 125, "#2563EB")
        archive_card = StatCard("Potentially Archivable Files", 20, 125, "#2563EB")
        
        stats_layout.addWidget(total_card, 1)
        stats_layout.addWidget(archive_card, 1)
        
        layout.addLayout(stats_layout)
        
        # Recent files tabs
        tabs_widget = QWidget()
        tabs_layout = QVBoxLayout()
        tabs_layout.setContentsMargins(20, 20, 20, 0)
        
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setSpacing(0)
        
        for tab_name in ["Recent", "Favorite", "Shared"]:
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
        
        # Recent files table
        recent_columns = ["", "File Name", "Date Accessed", "File Location"]
        recent_data = [
            ("Research_Paper", "10/12/2025", "../../Documents"),
            ("example_file", "8/11/2025", "../../Documents"),
            ("Example_video", "7/11/2025", "../../Video"),
            ("Example_image", "5/9/2025", "../../Image")
        ]
        
        recent_table = FileTableWidget(recent_columns, recent_data)
        tabs_layout.addWidget(recent_table)
        
        tabs_widget.setLayout(tabs_layout)
        layout.addWidget(tabs_widget)
        
        view.setLayout(layout)
        self.content_stack.addWidget(view)
    
    def create_statistics_view(self):
        """Statistics view (Image 5)"""
        view = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Top row - pie charts and stats
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        
        # Left column - pie charts
        charts_column = QVBoxLayout()
        charts_column.setSpacing(15)
        
        file_types_data = [
            ("Text-Based files:\n.doc, .docx, .edit, .rtf, .txt, etc...", 45),
            ("Image & Video files:\n.mp4, .mov, .avi, .mkv, etc...", 30),
            ("Developer & Code files:\n.html, .css, js, .py, .java, etc...", 25)
        ]
        charts_column.addWidget(PieChartWidget("Distribution of File Types within this PC", file_types_data))
        
        location_data = [
            ("Documents Folder", 60),
            ("Pictures Folder", 20),
            ("Video Folder", 20)
        ]
        charts_column.addWidget(PieChartWidget("Distribution of Files in a Location within this PC", location_data))
        
        top_row.addLayout(charts_column, 2)
        
        # Right column - stats cards
        stats_column = QVBoxLayout()
        stats_column.setSpacing(15)
        
        total_card = StatCard("Total File Size", 20, 125, "#2563EB")
        archive_card = StatCard("Archivable Files", 20, 125, "#2563EB")
        
        # Feature usage card
        usage_card = QWidget()
        usage_layout = QVBoxLayout()
        usage_layout.setContentsMargins(20, 15, 20, 15)
        
        usage_title = QLabel("Application's Feature Usage")
        usage_title.setStyleSheet("color: #C0C0C0; font-size: 14px; font-weight: bold;")
        usage_layout.addWidget(usage_title)
        
        # Smart Organise
        organise_label = QLabel("Smart Organise")
        organise_label.setStyleSheet("color: #E0E0E0; font-size: 16px; font-weight: bold; margin-top: 10px;")
        usage_layout.addWidget(organise_label)
        
        organise_stats = QHBoxLayout()
        usage_count = QLabel("Number of usage: 10")
        usage_count.setStyleSheet("color: #C0C0C0; font-size: 12px;")
        last_used = QLabel("Last used: 10 days ago")
        last_used.setStyleSheet("color: #888888; font-size: 12px;")
        organise_stats.addWidget(usage_count)
        organise_stats.addStretch()
        organise_stats.addWidget(last_used)
        usage_layout.addLayout(organise_stats)
        
        # Smart Archive
        archive_label = QLabel("Smart Archive")
        archive_label.setStyleSheet("color: #E0E0E0; font-size: 16px; font-weight: bold; margin-top: 15px;")
        usage_layout.addWidget(archive_label)
        
        archive_stats = QHBoxLayout()
        archive_count = QLabel("Number of usage: 5")
        archive_count.setStyleSheet("color: #C0C0C0; font-size: 12px;")
        archive_last = QLabel("Last used: 20 days ago")
        archive_last.setStyleSheet("color: #888888; font-size: 12px;")
        archive_stats.addWidget(archive_count)
        archive_stats.addStretch()
        archive_stats.addWidget(archive_last)
        usage_layout.addLayout(archive_stats)
        
        usage_card.setLayout(usage_layout)
        usage_card.setStyleSheet("""
            QWidget {
                background-color: #2D3748;
                border-radius: 8px;
            }
        """)
        
        stats_column.addWidget(total_card)
        stats_column.addWidget(archive_card)