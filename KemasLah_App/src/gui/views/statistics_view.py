import os
import shutil
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea) # Import QScrollArea
from PyQt6.QtCore import QDir, Qt      # Import Qt
from ..widgets.pie_chart import PieChartWidget
from ..widgets.stat_card import StatCard

class StatisticsView(QWidget):
    def __init__(self):
        super().__init__()
        self.stats = self.calculate_stats()
        self.init_ui()
        
    def calculate_stats(self):
        # ... (Keep your existing calculate_stats method exactly the same) ...
        # I am omitting the logic here to save space, but DO NOT DELETE IT from your file.
        # Just copy-paste the method from the previous successful version.
        home = QDir.homePath()
        paths_to_scan = {
            "Documents": os.path.join(home, "Documents"),
            "Pictures": os.path.join(home, "Pictures"),
            "Videos": os.path.join(home, "Videos"),
            "Music": os.path.join(home, "Music"),
            "Downloads": os.path.join(home, "Downloads")
        }
        type_counts = {"Text": 0, "Media": 0, "Code": 0, "Other": 0}
        location_sizes = {k: 0 for k in paths_to_scan.keys()}
        archivable_size = 0
        total_scanned_size = 0
        now = time.time()
        archive_threshold = 180 * 24 * 60 * 60 
        ext_map = {
            'text': ['.doc', '.docx', '.txt', '.pdf', '.rtf', '.md', '.xlsx', '.pptx'],
            'media': ['.jpg', '.png', '.mp4', '.mov', '.avi', '.mp3', '.wav', '.mkv', '.gif'],
            'code': ['.py', '.html', '.css', '.js', '.java', '.cpp', '.c', '.json', '.xml']
        }
        for category, path in paths_to_scan.items():
            if not os.path.exists(path): continue
            for root, _, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        stats = os.stat(file_path)
                        size = stats.st_size
                        location_sizes[category] += size
                        total_scanned_size += size
                        if (now - stats.st_mtime) > archive_threshold: archivable_size += size
                        _, ext = os.path.splitext(file)
                        ext = ext.lower()
                        if ext in ext_map['text']: type_counts["Text"] += 1
                        elif ext in ext_map['media']: type_counts["Media"] += 1
                        elif ext in ext_map['code']: type_counts["Code"] += 1
                        else: type_counts["Other"] += 1
                    except: continue
        try:
            total_disk, used_disk, free_disk = shutil.disk_usage(home)
            sys_total_gb = total_disk // (2**30)
            sys_used_gb = used_disk // (2**30)
        except:
            sys_total_gb, sys_used_gb = 500, 250
        return {
            "types": type_counts, "locations": location_sizes,
            "archivable_gb": archivable_size / (2**30), "total_scanned_gb": total_scanned_size / (2**30),
            "sys_total_gb": sys_total_gb, "sys_used_gb": sys_used_gb
        }

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Main Horizontal Layout (Left: Scrollable Charts, Right: Fixed Stats)
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        
        # --- LEFT COLUMN: SCROLL AREA ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Remove border and make background transparent to match theme
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #2D3748;
                width: 8px;
                margin: 0px; 
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4A5568;
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        # Container for the charts
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        charts_layout = QVBoxLayout(scroll_content)
        charts_layout.setContentsMargins(0, 0, 10, 0) # Right padding for scrollbar space
        charts_layout.setSpacing(20)
        
        # 1. Chart: File Types
        total_files = sum(self.stats["types"].values())
        if total_files == 0: total_files = 1
        t = self.stats["types"]
        file_types_data = [
            (f"Text-Based\n({t['Text']})", (t['Text']/total_files)*100),
            (f"Media\n({t['Media']})", (t['Media']/total_files)*100),
            (f"Code\n({t['Code']})", (t['Code']/total_files)*100),
            (f"Other\n({t['Other']})", (t['Other']/total_files)*100)
        ]
        file_types_data = [item for item in file_types_data if item[1] > 0]
        charts_layout.addWidget(PieChartWidget("Distribution of File Types", file_types_data))
        
        # 2. Chart: Locations
        l = self.stats["locations"]
        total_loc_size = sum(l.values())
        if total_loc_size == 0: total_loc_size = 1
        location_data = []
        for name, size_bytes in l.items():
            if size_bytes > 0:
                percentage = (size_bytes / total_loc_size) * 100
                if percentage > 1:
                    location_data.append((f"{name}", percentage))
        charts_layout.addWidget(PieChartWidget("Storage Used by Location", location_data))
        
        # Set the content into the scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add Scroll Area to Main Row (Ratio 2)
        top_row.addWidget(scroll_area, 2)
        
        # --- RIGHT COLUMN: STAT CARDS (Fixed) ---
        stats_column = QVBoxLayout()
        stats_column.setSpacing(15)
        
        total_card = StatCard("Local Disk (C:)", self.stats["sys_used_gb"], self.stats["sys_total_gb"], "#2563EB")
        
        archivable_gb = round(self.stats["archivable_gb"], 1)
        scanned_total_gb = round(self.stats["total_scanned_gb"], 1)
        if scanned_total_gb == 0: scanned_total_gb = 1
        archive_card = StatCard("Archivable Files (>6mo)", archivable_gb, scanned_total_gb, "#8B5CF6")
        
        # Feature usage card (Dummy)
        usage_card = QWidget()
        usage_layout = QVBoxLayout()
        usage_layout.setContentsMargins(20, 15, 20, 15)
        usage_title = QLabel("Application's Feature Usage")
        usage_title.setStyleSheet("color: #C0C0C0; font-size: 14px; font-weight: bold;")
        usage_layout.addWidget(usage_title)
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
        usage_card.setStyleSheet("QWidget { background-color: #2D3748; border-radius: 8px; }")
        
        stats_column.addWidget(total_card)
        stats_column.addWidget(archive_card)
        stats_column.addWidget(usage_card)
        
        # Add Right Column to Main Row (Ratio 1)
        top_row.addLayout(stats_column, 1)

        layout.addLayout(top_row)
        self.setLayout(layout)