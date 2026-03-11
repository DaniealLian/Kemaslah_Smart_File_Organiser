import urllib.request
import socket
import os         # NEW: Added for cloud paths
import shutil     # NEW: Added to copy the file
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QDateTimeEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDateTime

# FIXED: Uncommented the real database function import
from auth.database import share_file 

def is_connected():
    """Improved check: Attempts to resolve a common domain to verify internet access."""
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        return True
    except OSError:
        pass
    return False

class ShareFileDialog(QDialog):
    def __init__(self, file_path, current_user_email, is_guest=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.current_user_email = current_user_email
        self.is_guest = is_guest
        
        self.setWindowTitle("Share File")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog { background-color: #1A202C; color: white; }
            QLabel { color: #CBD5E0; font-size: 13px; }
            QLineEdit, QComboBox, QDateTimeEdit { 
                background-color: #0B1426; color: white; 
                border: 1px solid #4A5568; border-radius: 5px; padding: 8px; 
            }
            QPushButton { 
                background-color: #3182CE; color: white; 
                border-radius: 5px; padding: 10px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #2B6CB0; }
            QPushButton:disabled { background-color: #4A5568; color: #A0AEC0; }
        """)

        layout = QVBoxLayout(self)
        title = QLabel(f"Sharing: {file_path.split('/')[-1]}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Share with (Email):"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter user's email")
        layout.addWidget(self.email_input)

        layout.addWidget(QLabel("Permissions (RBAC):"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["View", "Comment", "Edit"])
        layout.addWidget(self.role_combo)

        self.exp_checkbox = QCheckBox("Set Expiration Date")
        self.exp_checkbox.setStyleSheet("color: #CBD5E0; margin-top: 10px;")
        self.exp_checkbox.toggled.connect(self.toggle_expiration)
        layout.addWidget(self.exp_checkbox)

        self.date_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(7))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setEnabled(False)
        layout.addWidget(self.date_edit)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: transparent; border: 1px solid #4A5568;")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.share_btn = QPushButton("Share File")
        self.share_btn.clicked.connect(self.handle_share)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.share_btn)
        layout.addLayout(btn_layout)

    def toggle_expiration(self, checked):
        self.date_edit.setEnabled(checked)

    def handle_share(self):
        if self.is_guest or not self.current_user_email:
            QMessageBox.warning(self, "Access Denied", "Guests cannot share files. Please log in to an account.")
            return

        if not is_connected():
            QMessageBox.critical(self, "Network Error", "You must be connected to the internet to share files.")
            return

        target_email = self.email_input.text().strip()
        if not target_email:
            QMessageBox.warning(self, "Error", "Please enter an email address.")
            return

        role = self.role_combo.currentText()
        expiration = None
        if self.exp_checkbox.isChecked():
            expiration = self.date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        # FIXED: Removed the dummy success = True and enabled the real database call
        success = share_file(self.file_path, self.current_user_email, target_email, role, expiration)
        
        if success:
            # --- NEW: CLOUD STORAGE SIMULATION ---
            try:
                # 1. Create a Cloud_Storage folder in your project directory
                cloud_dir = os.path.join(os.getcwd(), "Cloud_Storage")
                os.makedirs(cloud_dir, exist_ok=True)
                
                # --- FIX 2: PREVENT NAME COLLISIONS IN CLOUD ---
                # We prepend the owner's email to the filename so files with the same name don't overwrite!
                file_name = os.path.basename(self.file_path)
                cloud_file_name = f"{self.current_user_email}_{file_name}"
                cloud_path = os.path.join(cloud_dir, cloud_file_name)
                
                shutil.copy2(self.file_path, cloud_path)
                # -----------------------------------------------
            except Exception as e:
                print(f"Failed to upload to simulated cloud: {e}")
            # --------------------------------------

            QMessageBox.information(self, "Success", f"File shared with {target_email} as '{role}'.")
            self.accept()
        else:
            QMessageBox.critical(self, "Database Error", "Failed to share the file.")