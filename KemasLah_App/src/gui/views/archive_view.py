import os
import time
import datetime
import shutil
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QPushButton, QDialog, QLabel, QDateEdit, 
                             QProgressDialog, QMessageBox, QTreeWidget, 
                             QTreeWidgetItem, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QDir
from ..widgets.file_table import FileTableWidget


# ─── 1. DATE SELECTION DIALOG ──────────────────────────────────────────────
class DateSelectionDialog(QDialog):
    """Custom dialog matching your mockup to select start and end dates."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Archiving Date")
        self.setFixedSize(500, 280)
        self.setStyleSheet("background-color: #1A202C; color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        title_lbl = QLabel("Please enter the range of file age acceptable\nfor file archiving")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 16px; color: #E2E8F0;")
        layout.addWidget(title_lbl)

        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(15)

        self.start_date = QDateEdit()
        self.start_date.setDisplayFormat("MM/yyyy")
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet("""
            QDateEdit { border: 1px solid #3182CE; border-radius: 4px; padding: 8px; background-color: #2D3748; color: #A0AEC0; font-size: 14px; }
        """)

        sep_lbl = QLabel("–")
        sep_lbl.setStyleSheet("font-size: 16px; color: #A0AEC0;")

        self.end_date = QDateEdit()
        self.end_date.setDisplayFormat("MM/yyyy")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet("""
            QDateEdit { border: 1px solid #4A5568; border-radius: 4px; padding: 8px; background-color: #2D3748; color: #A0AEC0; font-size: 14px; }
        """)

        dates_layout.addWidget(self.start_date)
        dates_layout.addWidget(sep_lbl)
        dates_layout.addWidget(self.end_date)
        layout.addLayout(dates_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.continue_btn.setFixedHeight(40)
        self.continue_btn.setStyleSheet("""
            QPushButton { background-color: white; color: black; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        self.continue_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: red; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.continue_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_date_range(self):
        start_dt = datetime.datetime.combine(self.start_date.date().toPyDate(), datetime.datetime.min.time())
        end_dt = datetime.datetime.combine(self.end_date.date().toPyDate(), datetime.datetime.max.time())
        return start_dt.timestamp(), end_dt.timestamp()


# ─── 2. REVIEW & ACCEPT DIALOG (Matches Mockup) ────────────────────────────
class ArchiveReviewDialog(QDialog):
    """Shows the scanned top-level folders and files with checkboxes"""
    def __init__(self, paths, start_ts, end_ts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Archive")
        self.setFixedSize(850, 600)
        self.setStyleSheet("background-color: #212529; color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_lbl1 = QLabel("Thank you for waiting, smart archiving process is now complete.")
        title_lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl1.setStyleSheet("font-size: 18px; text-decoration: underline;")
        
        title_lbl2 = QLabel("Please choose to accept or decline the change:")
        title_lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl2.setStyleSheet("font-size: 18px; text-decoration: underline;")
        
        layout.addWidget(title_lbl1)
        layout.addWidget(title_lbl2)
        
        start_str = datetime.datetime.fromtimestamp(start_ts).strftime("%d/%m/%Y")
        end_str = datetime.datetime.fromtimestamp(end_ts).strftime("%d/%m/%Y")
        date_lbl = QLabel(f"Archiving date range: {start_str} to {end_str}")
        date_lbl.setStyleSheet("background-color: #1D4ED8; color: white; padding: 8px 12px; border-radius: 4px; font-size: 16px;")
        date_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(date_lbl)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Select All Checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setChecked(True)
        self.select_all_cb.setStyleSheet("""
            QCheckBox { color: #E0E0E0; font-size: 14px; font-weight: bold; padding: 5px 0px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #4A5568; border-radius: 4px; background-color: #2D3748; }
            QCheckBox::indicator:checked { background-color: #2563EB; border-color: #2563EB; }
        """)
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_cb)       
        
        # Hierarchical Tree (Grouped by Safe Folder Location)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Item Name", "Date Modified", "Type", "Size"])
        self.tree.setStyleSheet("""
            QTreeWidget { background-color: #D97706; color: white; border: none; font-size: 13px; }
            QHeaderView::section { background-color: #B45309; color: white; padding: 5px; font-weight: bold; border: none; }
            QTreeWidget::item { background-color: #D97706; padding: 8px; border-bottom: 1px solid #B45309; }
            QTreeWidget::item:has-children { background-color: #F59E0B; color: white; font-weight: bold; font-size: 15px; }
            QTreeWidget::indicator { width: 16px; height: 16px; }
        """)
        self.tree.setIndentation(20)
        
        # Group by root location (e.g. "Documents", "Downloads")
        groups = {}
        for path in paths:
            parent_dir = os.path.basename(os.path.dirname(path))
            if parent_dir not in groups: groups[parent_dir] = []
            groups[parent_dir].append(path)
            
        for parent_dir, group_paths in groups.items():
            # 1. Create the Location Group Header (NO CHECKBOX, JUST LABEL)
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"Location: {parent_dir}")
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable) 
            
            # 2. Create the Archivable Units (Folders or Files)
            for p in group_paths:
                item = QTreeWidgetItem(group_item)
                item.setText(0, os.path.basename(p))
                
                try:
                    stat = os.stat(p)
                    dt = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y")
                    item.setText(1, dt)
                    
                    if os.path.isdir(p):
                        item.setText(2, "File Folder")
                        item.setText(3, "-")
                        # Add AutoTristate so partial child selection works perfectly
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                        item.setCheckState(0, Qt.CheckState.Checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, p)
                        
                        # NEW: Recursively populate the contents of this folder so user can browse!
                        self._populate_tree(item, p)
                    else:
                        ext = os.path.splitext(p)[1] or "File"
                        item.setText(2, ext)
                        size = stat.st_size
                        size_str = f"{size / (1024*1024):.1f} MB" if size > 1024*1024 else f"{size / 1024:.1f} KB"
                        item.setText(3, size_str)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, p)
                except Exception:
                    pass
                
        self.tree.expandToDepth(1) # Expands the Location groups automatically
        
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.tree)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        accept_btn = QPushButton("Accept")
        accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        accept_btn.setFixedSize(150, 45)
        accept_btn.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-size: 18px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #047857; }
        """)
        accept_btn.clicked.connect(self.accept)
        
        decline_btn = QPushButton("Decline")
        decline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decline_btn.setFixedSize(150, 45)
        decline_btn.setStyleSheet("""
            QPushButton { background-color: #DC2626; color: white; font-size: 18px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        decline_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(accept_btn)
        btn_layout.addWidget(decline_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

    def _populate_tree(self, parent_item, path):
        """Recursively builds the internal structure of the Archivable Unit"""
        try:
            for entry in os.scandir(path):
                # Skip hidden files or the archive repository itself
                if entry.name.startswith('.') or "Kemaslah_Archive" in entry.name:
                    continue
                    
                item = QTreeWidgetItem(parent_item)
                item.setText(0, entry.name)
                
                try:
                    stat = entry.stat()
                    item.setText(1, datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y"))
                    
                    if entry.is_dir():
                        item.setText(2, "File Folder")
                        item.setText(3, "-")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                        item.setCheckState(0, Qt.CheckState.Checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, entry.path)
                        self._populate_tree(item, entry.path) # Recurse deeper
                    else:
                        ext = os.path.splitext(entry.name)[1] or "File"
                        item.setText(2, ext)
                        size = stat.st_size
                        size_str = f"{size / (1024*1024):.1f} MB" if size > 1024*1024 else f"{size / 1024:.1f} KB"
                        item.setText(3, size_str)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.CheckState.Checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, entry.path)
                except Exception:
                    continue
        except PermissionError:
            pass

    def get_selected_files(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            # Go through the Archivable Units inside the Location
            for j in range(group.childCount()):
                unit = group.child(j)
                self._collect_checked_paths(unit, selected)
        return selected

    def _collect_checked_paths(self, item, selected):
        state = item.checkState(0)
        if state == Qt.CheckState.Checked:
            # 1. Fully checked: Grab this path, and DO NOT recurse deeper.
            # Because shutil.move handles entire directories naturally!
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                selected.append(path)
        elif state == Qt.CheckState.PartiallyChecked:
            # 2. Partially checked: Recurse into children to grab specifically checked items
            for i in range(item.childCount()):
                self._collect_checked_paths(item.child(i), selected)

    def toggle_select_all(self, state):
        target_state = Qt.CheckState.Checked if state == 2 else Qt.CheckState.Unchecked
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            # Apply check state ONLY to the Archivable Units (it cascades automatically)
            for j in range(group.childCount()):
                group.child(j).setCheckState(0, target_state)


# ─── 3. SAFE BACKGROUND SCANNER (Top-Level Logic) ─────────────────────────
class ArchiveScannerWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, start_ts, end_ts):
        super().__init__()
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.is_running = True

        home = QDir.homePath()
        self.safe_folders = [
            os.path.join(home, "Documents"), os.path.join(home, "Downloads"),
            os.path.join(home, "Pictures"), os.path.join(home, "Videos"),
            os.path.join(home, "Music"), os.path.join(home, "Desktop")
        ]

    def run(self):
        matched_units = set() # Using a set to prevent duplicates
        try:
            for safe_folder in self.safe_folders:
                if not os.path.exists(safe_folder): continue

                # ONLY look at the top-level items inside the safe folder
                for entry in os.scandir(safe_folder):
                    if not self.is_running: break
                    if "Kemaslah_Archive" in entry.name: continue
                    
                    entry_path = entry.path

                    # 1. If it's a loose file, check it directly
                    if entry.is_file():
                        try:
                            if self.start_ts <= entry.stat().st_mtime <= self.end_ts:
                                matched_units.add(entry_path)
                        except: pass
                    
                    # 2. If it's a folder, search inside. If ANY file matches, add the WHOLE folder!
                    elif entry.is_dir():
                        folder_matches = False
                        for root, dirs, files in os.walk(entry_path):
                            if not self.is_running: break
                            for file in files:
                                try:
                                    full_path = os.path.join(root, file)
                                    stat_info = os.stat(full_path)
                                    if self.start_ts <= stat_info.st_mtime <= self.end_ts:
                                        folder_matches = True
                                        break # Found one, stop scanning this folder immediately
                                except: pass
                            if folder_matches: break
                            
                        if folder_matches:
                            matched_units.add(entry_path)

        except Exception as e:
            print(f"Scanner error: {e}")
        finally:
            self.finished.emit(list(matched_units))

    def stop(self):
        self.is_running = False


# ─── 4. MAIN ARCHIVE VIEW ──────────────────────────────────────────────────
class ArchiveView(QWidget):
    def __init__(self):
        super().__init__()
        self.scanner_worker = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Instructional Label
        self.info_lbl = QLabel("  Select files to archive by date range using the '⚙ Smart Archive' button above.")
        self.info_lbl.setStyleSheet("color: #A0AEC0; font-size: 14px; padding: 15px;")
        layout.addWidget(self.info_lbl)
        
        self.file_table = FileTableWidget()
        layout.addWidget(self.file_table)

    def open_date_dialog(self):
        dialog = DateSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            start_ts, end_ts = dialog.get_date_range()
            self.start_scanning(start_ts, end_ts)

    def start_scanning(self, start_ts, end_ts):
        self.file_table.table.blockSignals(True)
        self.file_table.table.setRowCount(0)
        self.file_table.select_all_cb.setChecked(False)
        self.file_table.table.blockSignals(False)
        
        self.info_lbl.setText("  Scanning folders... Please wait.")

        self.scanner_worker = ArchiveScannerWorker(start_ts, end_ts)
        self.scanner_worker.finished.connect(lambda units: self.on_scan_finished(units, start_ts, end_ts))
        self.scanner_worker.start()

    def on_scan_finished(self, matched_units, start_ts, end_ts):
        self.info_lbl.setText(f"  Found {len(matched_units)} archivable folders/files.")
        
        if not matched_units:
            QMessageBox.information(self, "Scan Complete", "No items found in this date range.")
            return
            
        # Launch the Review Dialog
        dialog = ArchiveReviewDialog(matched_units, start_ts, end_ts, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = dialog.get_selected_files()
            self.perform_archiving(selected_items)
            
    def perform_archiving(self, selected_items):
        if not selected_items:
            return
            
        # Define Archive Name scheme: e.g., "Archive_10_12_2025"
        today_str = datetime.datetime.now().strftime("%d_%m_%Y")
        archive_base = os.path.join(QDir.homePath(), "Documents", "Kemaslah_Archive")
        archive_dir = os.path.join(archive_base, f"Archive_{today_str}")
        
        os.makedirs(archive_dir, exist_ok=True)
        
        moved_count = 0
        for path in selected_items:
            if os.path.exists(path):
                try:
                    item_name = os.path.basename(path)
                    dest_path = os.path.join(archive_dir, item_name)
                    
                    # Prevent overwrite if two folders/files have the exact same name
                    base, ext = os.path.splitext(item_name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(archive_dir, f"{base}_copy{counter}{ext}")
                        counter += 1
                        
                    shutil.move(path, dest_path) # shutil.move automatically handles entire folders AND loose files!
                    moved_count += 1
                except Exception as e:
                    print(f"Failed to move {path}: {e}")
                    
        QMessageBox.information(self, "Archiving Complete", 
                                f"Successfully archived {moved_count} items into:\n{archive_dir}")
        
        # Display the newly created archive folder directly in the UI
        self.file_table.load_files(archive_dir)
        self.info_lbl.setText(f"  Viewing Archive: {archive_dir}")