import sqlite3
import os
import stat 
import shutil 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QHeaderView, QTableWidgetItem, QPushButton, QMessageBox,
                             QComboBox, QDialog, QDateTimeEdit, QCheckBox, QHBoxLayout,
                             QTextEdit)
from PyQt6.QtCore import Qt, QDateTime
from datetime import timezone
import datetime as dt_lib

# --- MONGODB IMPORTS ---
from pymongo import MongoClient
import gridfs
# ----------------------------

from auth.config import DB_PATH
from auth.database import revoke_file_share, update_file_share, request_extension, resolve_extension

# =====================================================================
# MUST UPDATE: Paste your MongoDB Atlas Connection String here!
MONGO_URI = "mongodb+srv://limzhihao0513_db_user:Ih9nx8rCN1700XUY@kemaslahcluster.815xmwv.mongodb.net/?appName=KemasLahCluster"
# =====================================================================

def create_readonly_item(text):
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item

class CommentDialog(QDialog):
    def __init__(self, file_path, cloud_file_name, current_user_email, is_owner=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.cloud_comment_name = cloud_file_name + ".comments"
        self.comment_file = file_path + ".comments"
        self.is_owner = is_owner 
        
        if self.is_owner:
            self.setWindowTitle(f"Viewing Comments: {os.path.basename(file_path)}")
        else:
            self.setWindowTitle(f"Review & Comment: {os.path.basename(file_path)}")
            
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1A202C; color: white; } 
            QLabel { color: white; font-weight: bold; margin-top: 10px; }
            QTextEdit { background-color: #0B1426; color: white; border: 1px solid #4A5568; padding: 5px; }
        """)
        
        layout = QVBoxLayout(self)
        
        # --- Header with External Open Button ---
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("File Content (Read-Only Preview):"))
        header_layout.addStretch()
        
        self.open_ext_btn = QPushButton("📄 Open File Externally")
        self.open_ext_btn.setStyleSheet("""
            QPushButton { background-color: #4A5568; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #2D3748; }
        """)
        self.open_ext_btn.clicked.connect(self.open_external)
        header_layout.addWidget(self.open_ext_btn)
        
        layout.addLayout(header_layout)
        
        # 1. Read-Only Content Viewer
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True) 
        self.content_view.setStyleSheet("background-color: #2D3748; color: #CBD5E0;")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content_view.setText(f.read())
        except UnicodeDecodeError:
            self.content_view.setStyleSheet("background-color: #2D3748; color: #A0AEC0; font-style: italic;")
            self.content_view.setText("This is a non-text file (e.g., Image, PDF, Document).\n\nPlease click the '📄 Open File Externally' button above to view the picture securely in your computer's default app.")
        except Exception as e:
            self.content_view.setText(f"Could not load preview:\n{e}")
            
        layout.addWidget(self.content_view, stretch=2)
        
        # 2. Comment Area
        layout.addWidget(QLabel("Collaborator Comments:" if self.is_owner else "Your Comments:"))
        self.comment_view = QTextEdit()
        
        if self.is_owner:
            self.comment_view.setReadOnly(True)
            self.comment_view.setStyleSheet("background-color: #2D3748; color: #68D391;") 
        else:
            self.comment_view.setPlaceholderText("Type your comments, feedback, or suggestions here while looking at the file...")
        
        if os.path.exists(self.comment_file):
            try:
                with open(self.comment_file, 'r', encoding='utf-8') as f:
                    self.comment_view.setText(f.read())
            except:
                pass
                
        layout.addWidget(self.comment_view, stretch=1)
        
        # 3. Save / Close Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if not self.is_owner:
            save_btn = QPushButton("Save Comments")
            save_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
            save_btn.clicked.connect(self.save_comments)
            btn_layout.addWidget(save_btn)
        else:
            close_btn = QPushButton("Close Viewer")
            close_btn.setStyleSheet("background-color: #4A5568; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
            close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(close_btn)
            
        layout.addLayout(btn_layout)

    def open_external(self):
        try:
            if not self.is_owner:
                os.chmod(self.file_path, stat.S_IREAD)
            os.startfile(self.file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file externally:\n{e}")
        
    def save_comments(self):
        try:
            with open(self.comment_file, 'w', encoding='utf-8') as f:
                f.write(self.comment_view.toPlainText())

            client = MongoClient(MONGO_URI)
            db = client["kemaslah_db"]
            fs = gridfs.GridFS(db)

            for old_c in fs.find({"filename": self.cloud_comment_name}):
                fs.delete(old_c._id)

            with open(self.comment_file, 'rb') as f:
                fs.put(f, filename=self.cloud_comment_name)

            QMessageBox.information(self, "Success", "Comments saved to the cloud successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save comments: {e}")

class ExpiryUpdateDialog(QDialog):
    def __init__(self, current_expiry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Expiration Date")
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QDialog { background-color: #1A202C; color: white; } 
            QLabel, QCheckBox { color: white; }
        """)
        layout = QVBoxLayout(self)
        
        self.exp_checkbox = QCheckBox("Set Expiration Date")
        self.exp_checkbox.setStyleSheet("color: white;")
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("background-color: #0B1426; color: white; border: 1px solid #4A5568; padding: 5px;")
        
        if current_expiry and str(current_expiry).strip() != "None" and str(current_expiry).strip() != "":
            self.exp_checkbox.setChecked(True)
            qt_date = QDateTime.fromString(str(current_expiry).replace("⚠️ EXPIRED (", "").replace(")", "").strip(), "yyyy-MM-dd HH:mm:ss")
            self.date_edit.setDateTime(qt_date)
        else:
            self.exp_checkbox.setChecked(False)
            self.date_edit.setDateTime(QDateTime.currentDateTime().addDays(7))
            self.date_edit.setEnabled(False)
        
        self.exp_checkbox.toggled.connect(self.date_edit.setEnabled)
        
        layout.addWidget(self.exp_checkbox)
        layout.addWidget(self.date_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("background-color: #3182CE; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def get_expiry(self):
        if self.exp_checkbox.isChecked():
            return self.date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        return None

class FileSharingView(QWidget):
    def __init__(self, current_user_email):
        super().__init__()
        self.user_email = current_user_email
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        self.title = QLabel("Shared Files")
        self.title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        self.subtitle = QLabel("Double-click a file to open it. Manage permissions for files you own.")
        self.subtitle.setStyleSheet("color: #A0AEC0; font-size: 14px; margin-bottom: 10px;")
        
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.subtitle)
        
        self.sync_btn = QPushButton("🔄 Sync Cloud Files")
        self.sync_btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB0; color: white; border-radius: 5px; padding: 10px 15px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #3182CE; }
        """)
        self.sync_btn.setToolTip("Pushes your edits to the cloud and pulls collaborator edits to you.")
        self.sync_btn.clicked.connect(self.sync_files)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.sync_btn, alignment=Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header_layout)
        
        # --- NEW: Changed to 8 columns and added 'Size' ---
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Direction", "File Name", "Size", "Shared With / By", "Role", "Expiration", "Shared On", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        # --------------------------------------------------
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1A202C; color: white; border: 1px solid #4A5568; border-radius: 5px; gridline-color: #2D3748; }
            QHeaderView::section { background-color: #2D3748; color: #CBD5E0; padding: 8px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #2D3748; }
        """)

        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)
        
        self.load_shared_files()

    def sync_files(self):
        cloud_dir = os.path.join(os.getcwd(), "Cloud_Storage")
        os.makedirs(cloud_dir, exist_ok=True)

        try:
            client = MongoClient(MONGO_URI)
            db = client["kemaslah_db"]
            fs = gridfs.GridFS(db)
            
            rows = db.shared_files.find({
                "$or": [
                    {"owner_email": self.user_email},
                    {"shared_with_email": self.user_email}
                ]
            })
            
            sync_count = 0
            
            for row in rows:
                original_path = row.get("file_path", "")
                owner_email = row.get("owner_email", "")
                role = row.get("role", "View")
                is_owner = (owner_email == self.user_email)
                
                file_name = os.path.basename(original_path)
                cloud_file_name = f"{owner_email}_{file_name}"
                
                local_path = original_path if is_owner else os.path.join(cloud_dir, cloud_file_name)

                cloud_file = fs.find_one({"filename": cloud_file_name}, sort=[("uploadDate", -1)])
                
                if cloud_file and os.path.exists(local_path):
                    cloud_dt = cloud_file.uploadDate.replace(tzinfo=timezone.utc)
                    local_mtime = os.path.getmtime(local_path)
                    local_dt = dt_lib.datetime.fromtimestamp(local_mtime, tz=timezone.utc)
                    
                    difference = (local_dt - cloud_dt).total_seconds()
                    
                    if difference > 5 and (is_owner or role == "Edit"):
                        reply = QMessageBox.question(self, 'Upload Changes', 
                                   f"You edited '{file_name}' locally.\nDo you want to push these edits to MongoDB for your team?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            for old_f in fs.find({"filename": cloud_file_name}):
                                fs.delete(old_f._id)
                            with open(local_path, 'rb') as f:
                                fs.put(f, filename=cloud_file_name, owner=owner_email)
                            sync_count += 1
                            
                    elif difference < -5:
                        reply = QMessageBox.question(self, 'Download Updates', 
                                   f"A collaborator updated '{file_name}' in the cloud.\nDo you want to download their changes?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            try:
                                os.chmod(local_path, stat.S_IWRITE)
                            except Exception:
                                pass
                            with open(local_path, 'wb') as f:
                                f.write(cloud_file.read())
                            
                            os.utime(local_path, (cloud_dt.timestamp(), cloud_dt.timestamp()))
                            sync_count += 1

                cloud_comment_name = f"{cloud_file_name}.comments"
                local_comment_path = local_path + ".comments"
                cloud_comment = fs.find_one({"filename": cloud_comment_name}, sort=[("uploadDate", -1)])
                
                if cloud_comment:
                    if not os.path.exists(local_comment_path) or os.path.getmtime(local_comment_path) < cloud_comment.uploadDate.replace(tzinfo=timezone.utc).timestamp():
                        with open(local_comment_path, 'wb') as f:
                            f.write(cloud_comment.read())
                        sync_count += 1

            if sync_count > 0:
                QMessageBox.information(self, "Sync Complete", f"Successfully synchronized {sync_count} update(s) with MongoDB!")
            else:
                QMessageBox.information(self, "Sync", "All your files and comments are fully up to date.")
                
            self.load_shared_files()
                
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"An error occurred during sync:\n{e}")

    def load_shared_files(self):
        try:
            client = MongoClient(MONGO_URI)
            db = client["kemaslah_db"]
            
            rows = db.shared_files.find({
                "$or": [
                    {"owner_email": self.user_email},
                    {"shared_with_email": self.user_email}
                ]
            }).sort("shared_at", -1)
            
            self.table.setRowCount(0) 
            
            for row_data in rows:
                file_path = row_data.get("file_path", "")
                owner = row_data.get("owner_email", "")
                recipient = row_data.get("shared_with_email", "")
                role = row_data.get("role", "View")
                expiry = row_data.get("expiration_date", None)
                shared_at = row_data.get("shared_at", "")
                ext_status = row_data.get("extension_status", "None")
                req_date = row_data.get("requested_date", None)
                
                # --- NEW: Retrieve the size from the database ---
                file_size = row_data.get("file_size", "Unknown")
                # ------------------------------------------------
                
                is_expired = False
                if expiry and str(expiry).strip() != "None":
                    exp_qt = QDateTime.fromString(str(expiry), "yyyy-MM-dd HH:mm:ss")
                    if QDateTime.currentDateTime() > exp_qt:
                        is_expired = True
                
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                is_owner = owner.lower() == self.user_email.lower()
                direction = "Sent" if is_owner else "Received"
                partner = recipient if is_owner else owner
                file_name = os.path.basename(file_path)
                
                name_item = create_readonly_item(file_name)
                name_item.setData(Qt.ItemDataRole.UserRole, {"path": file_path, "owner": owner})

                # --- SHIFTED COLUMN PLACEMENTS ---
                self.table.setItem(row_idx, 0, create_readonly_item(direction))
                self.table.setItem(row_idx, 1, name_item) 
                self.table.setItem(row_idx, 2, create_readonly_item(file_size)) # NEW Size Column
                self.table.setItem(row_idx, 3, create_readonly_item(partner))
                self.table.setItem(row_idx, 6, create_readonly_item(str(shared_at)))
                # ---------------------------------
                
                if direction == "Received":
                    self.table.item(row_idx, 0).setForeground(Qt.GlobalColor.green)
                    self.table.setItem(row_idx, 4, create_readonly_item(str(role)))
                    
                    expiry_display = str(expiry) if expiry else "No Expiry"
                    if is_expired:
                        expiry_display = "⚠️ EXPIRED (" + expiry_display + ")"
                    self.table.setItem(row_idx, 5, create_readonly_item(expiry_display))
                    
                    if is_expired:
                        self.table.item(row_idx, 5).setForeground(Qt.GlobalColor.red)
                    
                    if expiry and str(expiry).strip() != "None":
                        if ext_status == "Pending":
                            self.table.setItem(row_idx, 7, create_readonly_item("⏳ Pending Request"))
                            self.table.item(row_idx, 7).setForeground(Qt.GlobalColor.yellow)
                        else:
                            btn_text = "Renew Access" if is_expired else "Request Extension"
                            req_btn = QPushButton(btn_text)
                            req_btn.setStyleSheet("background-color: #DD6B20; color: white; border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold;")
                            if is_expired:
                                req_btn.setStyleSheet("background-color: #E53E3E; color: white; border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold;")
                            req_btn.clicked.connect(lambda _, fp=file_path, o=owner: self.handle_request_extension(fp, o))
                            self.table.setCellWidget(row_idx, 7, req_btn)
                    else:
                        self.table.setItem(row_idx, 7, create_readonly_item("-"))
                        
                else:
                    self.table.item(row_idx, 0).setForeground(Qt.GlobalColor.cyan)
                    
                    role_combo = QComboBox()
                    role_combo.addItems(["View", "Comment", "Edit"])
                    role_combo.setStyleSheet("background-color: #2D3748; color: white; border: 1px solid #4A5568;")
                    role_combo.setCurrentText(str(role))
                    role_combo.currentTextChanged.connect(
                        lambda text, fp=file_path, te=recipient, ce=expiry: self.update_role(fp, te, text, ce)
                    )
                    self.table.setCellWidget(row_idx, 4, role_combo)

                    expiry_text = str(expiry) if expiry else "No Expiry"
                    if is_expired:
                        expiry_text = "⚠️ EXPIRED (" + expiry_text + ")"
                        
                    expiry_btn = QPushButton(expiry_text)
                    if ext_status == "Pending":
                        expiry_btn.setText("⚠️ Review Request")
                        expiry_btn.setStyleSheet("background-color: #D69E2E; color: black; font-weight: bold; border-radius: 4px; padding: 4px;")
                        expiry_btn.clicked.connect(lambda _, fp=file_path, te=recipient, rd=req_date, ce=expiry: self.open_review_dialog(fp, te, rd, ce))
                    else:
                        expiry_btn.setStyleSheet("""
                            QPushButton { background-color: #2D3748; color: white; border: 1px solid #4A5568; border-radius: 4px; padding: 4px; text-align: left; }
                            QPushButton:hover { background-color: #4A5568; border: 1px solid #3182CE; }
                        """)
                        if is_expired:
                            expiry_btn.setStyleSheet("background-color: #742A2A; color: white; border: 1px solid #FC8181; border-radius: 4px; padding: 4px; text-align: left;")
                        expiry_btn.clicked.connect(lambda _, fp=file_path, te=recipient, cr=role, ce=expiry: self.open_expiry_dialog(fp, te, cr, ce))
                    
                    self.table.setCellWidget(row_idx, 5, expiry_btn)

                    revoke_btn = QPushButton("Revoke Access")
                    revoke_btn.setStyleSheet("""
                        QPushButton { background-color: #E53E3E; color: white; border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold; }
                        QPushButton:hover { background-color: #C53030; }
                    """)
                    revoke_btn.clicked.connect(lambda _, fp=file_path, t=recipient: self.handle_revoke(fp, t))
                    self.table.setCellWidget(row_idx, 7, revoke_btn)
                
        except Exception as e:
            print(f"Error loading shared files from MongoDB: {e}")

    def handle_request_extension(self, file_path, owner_email):
        dialog = ExpiryUpdateDialog(None, self)
        dialog.setWindowTitle("Request Expiration Extension")
        dialog.exp_checkbox.setChecked(True)
        dialog.exp_checkbox.setEnabled(False) 
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_date = dialog.get_expiry()
            if request_extension(file_path, owner_email, self.user_email, new_date):
                QMessageBox.information(self, "Request Sent", f"Your request to extend access until {new_date} has been sent to the owner.")
                self.load_shared_files()
            else:
                QMessageBox.critical(self, "Error", "Failed to send extension request.")

    def open_review_dialog(self, file_path, target_email, requested_date, current_expiry):
        reply = QMessageBox.question(self, 'Review Extension Request', 
                   f"The user {target_email} has requested to extend their access until:\n\n{requested_date}\n\nDo you approve this extension?",
                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Yes:
            if resolve_extension(file_path, self.user_email, target_email, requested_date, "Approved"):
                QMessageBox.information(self, "Approved", "Extension approved! The file expiration date has been updated.")
                self.load_shared_files()
        elif reply == QMessageBox.StandardButton.No:
            if resolve_extension(file_path, self.user_email, target_email, None, "Rejected"):
                QMessageBox.warning(self, "Rejected", "Extension request rejected. The original expiration date remains.")
                self.load_shared_files()

    def on_double_click(self, row, col):
        direction_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        
        if not direction_item or not name_item:
            return
            
        direction = direction_item.text()
        file_name = name_item.text()
        
        data = name_item.data(Qt.ItemDataRole.UserRole)
        original_path = data["path"]
        owner_email = data["owner"]
        cloud_file_name = f"{owner_email}_{file_name}"
        
        # --- SHIFTED: Check Expiration in Column 5 ---
        expiry_item = self.table.item(row, 5)
        if expiry_item and expiry_item.text():
            raw_text = expiry_item.text().replace("⚠️ EXPIRED (", "").replace(")", "").strip()
            if raw_text != "No Expiry" and raw_text != "None":
                expiry_date = QDateTime.fromString(raw_text, "yyyy-MM-dd HH:mm:ss")
                if QDateTime.currentDateTime() > expiry_date:
                    reply = QMessageBox.question(self, "Access Expired", 
                                               "Your access to this file has expired.\n\nWould you like to request renewed access from the owner?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        self.handle_request_extension(original_path, owner_email)
                    return 
        # ---------------------------------------------

        if direction == "Sent":
            path_to_open = original_path
            
            try:
                client = MongoClient(MONGO_URI)
                db = client["kemaslah_db"]
                fs = gridfs.GridFS(db)
                cloud_comment = fs.find_one({"filename": cloud_file_name + ".comments"}, sort=[("uploadDate", -1)])
                if cloud_comment:
                    with open(original_path + ".comments", 'wb') as f:
                        f.write(cloud_comment.read())
            except Exception:
                pass
            
            comment_path = original_path + ".comments"
            if os.path.exists(comment_path):
                reply = QMessageBox.question(self, 'Comments Found', 
                                           "Your collaborator has left comments on this file. Do you want to read them now?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    dialog = CommentDialog(path_to_open, cloud_file_name, self.user_email, is_owner=True, parent=self)
                    dialog.exec()
                    return 
        else:
            cloud_dir = os.path.join(os.getcwd(), "Cloud_Storage")
            os.makedirs(cloud_dir, exist_ok=True)
            path_to_open = os.path.join(cloud_dir, cloud_file_name)
            
            try:
                client = MongoClient(MONGO_URI)
                db = client["kemaslah_db"]
                fs = gridfs.GridFS(db)
                cloud_file = fs.find_one({"filename": cloud_file_name}, sort=[("uploadDate", -1)])
                
                if cloud_file:
                    if os.path.exists(path_to_open):
                        try: os.chmod(path_to_open, stat.S_IWRITE)
                        except Exception: pass
                            
                    with open(path_to_open, 'wb') as f:
                        f.write(cloud_file.read())
            except Exception as e:
                print(f"MongoDB Download Error: {e}")
            
            if os.path.exists(path_to_open):
                # --- SHIFTED: Check Role in Column 4 ---
                role_item = self.table.item(row, 4) 
                if role_item:
                    role = role_item.text()
                    
                    if role == "Comment":
                        dialog = CommentDialog(path_to_open, cloud_file_name, self.user_email, is_owner=False, parent=self)
                        dialog.exec()
                        return 
                    
                    try:
                        if role == "View": os.chmod(path_to_open, stat.S_IREAD)
                        elif role == "Edit": os.chmod(path_to_open, stat.S_IWRITE)
                    except Exception as e:
                        print(f"Failed to set file permissions: {e}")
            
        try:
            if os.path.exists(path_to_open):
                os.startfile(path_to_open)
            else:
                QMessageBox.warning(self, "File Not Found", f"The file has been moved or deleted:\n{path_to_open}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def update_role(self, file_path, target_email, new_role, current_expiry):
        if not update_file_share(file_path, self.user_email, target_email, new_role, current_expiry):
            QMessageBox.critical(self, "Error", "Failed to update role.")
            self.load_shared_files() 

    def open_expiry_dialog(self, file_path, target_email, current_role, current_expiry):
        dialog = ExpiryUpdateDialog(current_expiry, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_expiry = dialog.get_expiry()
            if new_expiry != current_expiry:
                if update_file_share(file_path, self.user_email, target_email, current_role, new_expiry):
                    self.load_shared_files() 
                else:
                    QMessageBox.critical(self, "Error", "Failed to update expiration date.")

    def handle_revoke(self, file_path, target_email):
        reply = QMessageBox.question(self, 'Confirm Revoke', 
                                   f"Are you sure you want to stop sharing this file with {target_email}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if revoke_file_share(file_path, self.user_email, target_email):
                QMessageBox.information(self, "Success", "Access revoked successfully.")
                self.load_shared_files() 
            else:
                QMessageBox.critical(self, "Error", "Failed to revoke access.")

    def update_translations(self, lang_code):
        pass