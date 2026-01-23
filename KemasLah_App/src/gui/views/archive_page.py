import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QProgressBar, QSpinBox, QFrame, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer

class ArchivePage(QWidget):
    def __init__(self):
        super().__init__()

        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # --- 1. HEADER SECTION ---
        header_layout = QHBoxLayout()
        
        title_block = QVBoxLayout()
        title = QLabel("Smart Archiving")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        subtitle = QLabel("Identify unused files and compress them to save space.")
        subtitle.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        
        header_layout.addLayout(title_block)
        header_layout.addStretch()
        
        # Savings Card (Visual Motivation)
        self.savings_card = self.create_savings_card()
        header_layout.addWidget(self.savings_card)
        
        self.layout.addLayout(header_layout)

        # --- 2. CONTROL PANEL (Threshold Settings) ---
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; padding: 10px;")
        control_layout = QHBoxLayout(control_frame)

        lbl_setting = QLabel("Find files not opened in the last:")
        lbl_setting.setStyleSheet("color: white; font-size: 14px;")
        
        self.days_spinner = QSpinBox()
        self.days_spinner.setRange(30, 3650)
        self.days_spinner.setValue(90) # Default from requirements
        self.days_spinner.setSuffix(" Days")
        self.days_spinner.setFixedWidth(120)
        self.days_spinner.setStyleSheet("""
            QSpinBox { background-color: #3e3e3e; color: white; border: 1px solid #555; padding: 5px; font-size: 14px; }
            QSpinBox::up-button, QSpinBox::down-button { width: 20px; }
        """)

        self.btn_scan = QPushButton("🔍 Start Scan")
        self.btn_scan.setFixedWidth(150)
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan_simulation)
        self.btn_scan.setStyleSheet("""
            QPushButton { background-color: #0078D4; color: white; font-weight: bold; border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #1084d9; }
        """)

        control_layout.addWidget(lbl_setting)
        control_layout.addWidget(self.days_spinner)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_scan)
        
        self.layout.addWidget(control_frame)

        # --- 3. PROGRESS BAR (Hidden by default) ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #3e3e3e; height: 8px; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #0078D4; border-radius: 4px; }
        """)
        self.layout.addWidget(self.progress_bar)

        # --- 4. RESULTS TABLE ---
        lbl_results = QLabel("Scan Results")
        lbl_results.setStyleSheet("color: #cccccc; font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(lbl_results)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File Name", "Location", "Last Accessed", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: white; border: 1px solid #333; border-radius: 5px; }
            QHeaderView::section { background-color: #2b2b2b; color: #aaa; padding: 8px; border: none; }
            QTableWidget::item { padding: 5px; }
        """)
        self.layout.addWidget(self.table)

        # --- 5. FOOTER ACTIONS ---
        footer_layout = QHBoxLayout()
        
        self.lbl_total_size = QLabel("Total Potential Savings: 0 MB")
        self.lbl_total_size.setStyleSheet("color: #D83B01; font-weight: bold; font-size: 16px;")
        
        self.btn_archive = QPushButton("📦 Archive Selected Files")
        self.btn_archive.setEnabled(False) # Disabled until scan finishes
        self.btn_archive.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_archive.setFixedHeight(40)
        self.btn_archive.clicked.connect(self.confirm_archival)
        self.btn_archive.setStyleSheet("""
            QPushButton { background-color: #D83B01; color: white; font-weight: bold; border-radius: 5px; padding: 0 20px; }
            QPushButton:disabled { background-color: #444; color: #888; }
            QPushButton:hover { background-color: #ea4a1f; }
        """)

        footer_layout.addWidget(self.lbl_total_size)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_archive)
        
        self.layout.addLayout(footer_layout)

    def create_savings_card(self):
        """Small Widget showing total history of savings"""
        card = QFrame()
        card.setFixedSize(180, 70)
        card.setStyleSheet("background-color: #2b2b2b; border-radius: 8px; border-left: 4px solid #107C10;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 10, 10)
        
        lbl = QLabel("Lifetime Savings")
        lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        val = QLabel("0.00 GB")
        val.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        
        layout.addWidget(lbl)
        layout.addWidget(val)
        return card

    def start_scan_simulation(self):
        """Simulates the scanning process with visual feedback"""
        self.btn_scan.setEnabled(False)
        self.table.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create a timer to fake a loading animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_val = 0
        self.timer.start(50) # Update every 50ms

    def update_progress(self):
        self.progress_val += 2
        self.progress_bar.setValue(self.progress_val)
        
        if self.progress_val >= 100:
            self.timer.stop()
            self.btn_scan.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.populate_dummy_results()
            self.btn_archive.setEnabled(True)

    def populate_dummy_results(self):
        """Fills table with fake data for User Interface testing"""
        # Data format: Name, Path, Date, Size
        dummy_data = [
            ("Old_Project_Draft.docx", "C:/Users/Danieal/Documents", "2023-01-15", "5.2 MB"),
            ("Setup_Installer_v1.exe", "C:/Users/Danieal/Downloads", "2022-11-20", "150 MB"),
            ("Meeting_Recording.mp4", "C:/Users/Danieal/Videos", "2023-03-10", "450 MB"),
            ("Scan_001.pdf", "C:/Users/Danieal/Documents", "2023-05-02", "12 MB"),
        ]
        
        self.table.setRowCount(len(dummy_data))
        for row, (name, path, date, size) in enumerate(dummy_data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(path))
            self.table.setItem(row, 2, QTableWidgetItem(date))
            self.table.setItem(row, 3, QTableWidgetItem(size))
            
        self.lbl_total_size.setText("Total Potential Savings: 617.2 MB")

    def confirm_archival(self):
        """Shows the confirmation dialog as required in Chapter 4"""
        msg = QMessageBox()
        msg.setWindowTitle("Confirm Archival")
        msg.setText(f"Are you sure you want to compress {self.table.rowCount()} files?")
        msg.setInformativeText("These files will be moved to a single ZIP archive. You can restore them later.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Apply Dark Mode to the Message Box (Optional/Advanced, but good for consistency)
        msg.setStyleSheet("QLabel{color: white;} QMessageBox{background-color: #2b2b2b;}")
        
        ret = msg.exec()
        if ret == QMessageBox.StandardButton.Yes:
            # Clear table to simulate "Done"
            self.table.setRowCount(0)
            self.lbl_total_size.setText("Total Potential Savings: 0 MB")
            self.btn_archive.setEnabled(False)
            QMessageBox.information(self, "Success", "Files successfully archived!")