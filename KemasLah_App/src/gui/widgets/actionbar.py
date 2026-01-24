from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class ActionBar(QWidget):
    # Define signals for each action
    action_clicked = pyqtSignal(str) # Emits "new", "cut", "copy", etc.
    smart_organise_clicked = pyqtSignal()

    def __init__(self, show_smart_button=True, button_text="Smart Organise"):
        super().__init__()
        self.init_ui(show_smart_button, button_text)
        
    def init_ui(self, show_smart_button, button_text):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Action buttons configuration: (Label, Signal Name)
        actions = [
            ("➕ New", "new"),
            ("✂ Cut", "cut"),
            ("📋 Copy", "copy"),
            ("📄 Paste", "paste"),
            ("✏ Rename", "rename"),
            ("⤴ Share", "share"),
            ("🗑 Delete", "delete")
        ]
        
        for text, action_name in actions:
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
                QPushButton:pressed {
                    background-color: #4A5568;
                }
            """)
            # Connect click to signal emission
            btn.clicked.connect(lambda checked, a=action_name: self.action_clicked.emit(a))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Smart Organise button
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
                QPushButton:hover { background-color: #1E40AF; }
            """)
            smart_btn.clicked.connect(self.smart_organise_clicked.emit)
            layout.addWidget(smart_btn)

        self.setLayout(layout)