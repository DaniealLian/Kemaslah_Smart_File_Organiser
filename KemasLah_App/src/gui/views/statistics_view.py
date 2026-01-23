from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from ..widgets.pie_chart import PieChartWidget
from ..widgets.stat_card import StatCard

class StatisticsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
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
        stats_column.addWidget(usage_card) # Ensure usage card is added

        top_row.addLayout(stats_column, 1)

        layout.addLayout(top_row)

        self.setLayout(layout)