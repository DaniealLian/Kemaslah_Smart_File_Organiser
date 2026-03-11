import sqlite3
import os
import stat 
import shutil 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QHeaderView, QTableWidgetItem, QPushButton, QMessageBox,
                             QComboBox, QDialog, QDateTimeEdit, QCheckBox, QHBoxLayout,
                             QTextEdit)
from PyQt6.QtCore import Qt, QDateTime

from auth.config import DB_PATH
from auth.database import revoke_file_share, update_file_share

def create_readonly_item(text):
    """Helper function to create a table item that cannot be typed into."""
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item

# --- UPDATED: CUSTOM COMMENT VIEWER (Supports ALL File Types & Owner Protections) ---
class CommentDialog(QDialog):
    """A custom viewer for reading and writing comments."""
    def __init__(self, file_path, current_user_email, is_owner=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.comment_file = file_path + ".comments"
        
        # NEW: Save the owner status so we can check it later!
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
        """Safely opens non-text files using Windows default programs."""
        try:
            # --- ONLY lock the file to Read-Only if the Collaborator is viewing it! ---
            if not self.is_owner:
                os.chmod(self.file_path, stat.S_IREAD)
            # -------------------------------------------------------------------------------
            
            os.startfile(self.file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file externally:\n{e}")
        
    def save_comments(self):
        try:
            with open(self.comment_file, 'w', encoding='utf-8') as f:
                f.write(self.comment_view.toPlainText())
            QMessageBox.information(self, "Success", "Comments saved to the cloud successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save comments: {e}")
# ------------------------------------------------------------------------

class ExpiryUpdateDialog(QDialog):
    """A mini pop-up dialog just for changing the expiration date."""
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
            qt_date = QDateTime.fromString(str(current_expiry), "yyyy-MM-dd HH:mm:ss")
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
        self.sync_btn.setToolTip("Pulls any edits made by other users back to your original files.")
        self.sync_btn.clicked.connect(self.sync_files)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.sync_btn, alignment=Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Direction", "File Name", "Shared With / By", "Role", "Expiration", "Shared On", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
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
        if not os.path.exists(cloud_dir):
            QMessageBox.information(self, "Sync", "No cloud storage folder found yet. Try sharing a file first!")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM SharedFiles WHERE owner_email = ?", (self.user_email,))
            rows = cursor.fetchall()
            conn.close()
            
            sync_count = 0
            for row in rows:
                original_path = row[0]
                file_name = os.path.basename(original_path)
                
                # --- FIX 2: Retrieve using the new collision-proof name ---
                cloud_file_name = f"{self.user_email}_{file_name}"
                cloud_path = os.path.join(cloud_dir, cloud_file_name)
                # ----------------------------------------------------------
                
                if os.path.exists(original_path) and os.path.exists(cloud_path):
                    cloud_mtime = os.path.getmtime(cloud_path)
                    orig_mtime = os.path.getmtime(original_path)
                    
                    if cloud_mtime > orig_mtime:
                        # --- FIX 3: PREVENT BLIND OVERWRITES ---
                        reply = QMessageBox.question(self, 'Confirm Sync', 
                                   f"The cloud version of '{file_name}' was updated by a collaborator.\nDo you want to overwrite your local file with their changes?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            try:
                                os.chmod(original_path, stat.S_IWRITE)
                            except Exception:
                                pass
                            shutil.copy2(cloud_path, original_path)
                            sync_count += 1
                        # ---------------------------------------
                        
                cloud_comment_path = cloud_path + ".comments"
                orig_comment_path = original_path + ".comments"
                
                if os.path.exists(cloud_comment_path):
                    shutil.copy2(cloud_comment_path, orig_comment_path)
                        
            if sync_count > 0:
                QMessageBox.information(self, "Sync Complete", f"Successfully synced {sync_count} updated file(s) and comments from the cloud!")
            else:
                QMessageBox.information(self, "Sync", "All your local files and comments are up to date with the cloud.")
                
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"An error occurred during sync:\n{e}")

    def load_shared_files(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT file_path, owner_email, shared_with_email, role, expiration_date, shared_at 
                FROM SharedFiles 
                WHERE owner_email = ? OR shared_with_email = ?
                ORDER BY shared_at DESC
            """, (self.user_email, self.user_email))
            
            rows = cursor.fetchall()
            self.table.setRowCount(0) 
            
            for row_data in rows:
                file_path, owner, recipient, role, expiry, shared_at = row_data
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                is_owner = owner.lower() == self.user_email.lower()
                direction = "Sent" if is_owner else "Received"
                partner = recipient if is_owner else owner
                file_name = os.path.basename(file_path)
                
                # --- FIX 2: Pass the owner email securely into the cell data ---
                name_item = create_readonly_item(file_name)
                name_item.setData(Qt.ItemDataRole.UserRole, {"path": file_path, "owner": owner})
                # ---------------------------------------------------------------

                self.table.setItem(row_idx, 0, create_readonly_item(direction))
                self.table.setItem(row_idx, 1, name_item) 
                self.table.setItem(row_idx, 2, create_readonly_item(partner))
                self.table.setItem(row_idx, 5, create_readonly_item(str(shared_at)))
                
                if direction == "Received":
                    self.table.item(row_idx, 0).setForeground(Qt.GlobalColor.green)
                else:
                    self.table.item(row_idx, 0).setForeground(Qt.GlobalColor.cyan)
                
                if is_owner:
                    role_combo = QComboBox()
                    role_combo.addItems(["View", "Comment", "Edit"])
                    role_combo.setStyleSheet("background-color: #2D3748; color: white; border: 1px solid #4A5568;")
                    role_combo.setCurrentText(str(role))
                    role_combo.currentTextChanged.connect(
                        lambda text, fp=file_path, te=recipient, ce=expiry: self.update_role(fp, te, text, ce)
                    )
                    self.table.setCellWidget(row_idx, 3, role_combo)

                    expiry_text = str(expiry) if expiry else "No Expiry"
                    expiry_btn = QPushButton(expiry_text)
                    expiry_btn.setStyleSheet("""
                        QPushButton { background-color: #2D3748; color: white; border: 1px solid #4A5568; border-radius: 4px; padding: 4px; text-align: left; }
                        QPushButton:hover { background-color: #4A5568; border: 1px solid #3182CE; }
                    """)
                    expiry_btn.clicked.connect(
                        lambda _, fp=file_path, te=recipient, cr=role, ce=expiry: self.open_expiry_dialog(fp, te, cr, ce)
                    )
                    self.table.setCellWidget(row_idx, 4, expiry_btn)

                    revoke_btn = QPushButton("Revoke Access")
                    revoke_btn.setStyleSheet("""
                        QPushButton { background-color: #E53E3E; color: white; border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold; }
                        QPushButton:hover { background-color: #C53030; }
                    """)
                    revoke_btn.clicked.connect(lambda _, fp=file_path, t=recipient: self.handle_revoke(fp, t))
                    self.table.setCellWidget(row_idx, 6, revoke_btn)
                else:
                    self.table.setItem(row_idx, 3, create_readonly_item(str(role)))
                    self.table.setItem(row_idx, 4, create_readonly_item(str(expiry) if expiry else "No Expiry"))
                    self.table.setItem(row_idx, 6, create_readonly_item("-"))
                
            conn.close()
        except sqlite3.Error as e:
            print(f"Error loading shared files: {e}")

    def on_double_click(self, row, col):
        direction_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        
        if not direction_item or not name_item:
            return
            
        direction = direction_item.text()
        file_name = name_item.text()
        
        # --- FIX 2: Unpack the data payload safely ---
        data = name_item.data(Qt.ItemDataRole.UserRole)
        original_path = data["path"]
        owner_email = data["owner"]
        # ---------------------------------------------
        
        # --- FIX 1: ENFORCE EXPIRATION DATE ---
        expiry_item = self.table.item(row, 4)
        if expiry_item and expiry_item.text() != "No Expiry":
            expiry_date = QDateTime.fromString(expiry_item.text(), "yyyy-MM-dd HH:mm:ss")
            if QDateTime.currentDateTime() > expiry_date:
                QMessageBox.warning(self, "Access Expired", "The expiration date for this file has passed. You can no longer open it.")
                return # Block the user completely
        # --------------------------------------

        if direction == "Sent":
            path_to_open = original_path
            
            comment_path = original_path + ".comments"
            if os.path.exists(comment_path):
                reply = QMessageBox.question(self, 'Comments Found', 
                                           "Your collaborator has left comments on this file. Do you want to read them now?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    dialog = CommentDialog(path_to_open, self.user_email, is_owner=True, parent=self)
                    dialog.exec()
                    return 
        else:
            cloud_dir = os.path.join(os.getcwd(), "Cloud_Storage")
            
            # --- FIX 2: Fetch using the new collision-proof name ---
            cloud_file_name = f"{owner_email}_{file_name}"
            path_to_open = os.path.join(cloud_dir, cloud_file_name)
            # -------------------------------------------------------
            
            if os.path.exists(path_to_open):
                role_item = self.table.item(row, 3) 
                if role_item:
                    role = role_item.text()
                    
                    if role == "Comment":
                        dialog = CommentDialog(path_to_open, self.user_email, is_owner=False, parent=self)
                        dialog.exec()
                        return 
                    
                    try:
                        if role == "View":
                            os.chmod(path_to_open, stat.S_IREAD)
                        elif role == "Edit":
                            os.chmod(path_to_open, stat.S_IWRITE)
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