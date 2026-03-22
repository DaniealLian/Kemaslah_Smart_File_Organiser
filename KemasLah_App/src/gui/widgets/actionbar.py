from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from auth.authentication_page import translate_text

class ActionBar(QWidget):
    # Define signals for each action
    action_clicked = pyqtSignal(str) 
    smart_organise_clicked = pyqtSignal()
    
    # --- NEW: Navigation Signals ---
    nav_back_clicked = pyqtSignal()
    nav_forward_clicked = pyqtSignal()

    def __init__(self, show_smart_button=True, button_text="Smart Organise"):
        super().__init__()
        self.init_ui(show_smart_button, button_text)
        
    def init_ui(self, show_smart_button, button_text):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        button_style = """
            QPushButton {
                padding: 8px 16px;
                background-color: #2D3748;
                color: #E0E0E0;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #3A4556; }
            QPushButton:pressed { background-color: #4A5568; }
            QPushButton:disabled { background-color: #1A202C; color: #4A5568; }
        """

        nav_btn_style = """
            QPushButton {
                padding: 8px 16px;
                background-color: #1976D2;
                color: #E0E0E0;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #09386B; }
            QPushButton:pressed { background-color: #09386B; }
            QPushButton:disabled { background-color: #1A202C; color: #4A5568; }
        """

        # --- NEW: Navigation Buttons ---
        self.back_btn = QPushButton("<")
        self.back_btn.setStyleSheet(nav_btn_style)
        self.back_btn.setFixedWidth(40) # Make them square-ish
        self.back_btn.clicked.connect(self.nav_back_clicked.emit)
        layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton(">")
        self.forward_btn.setStyleSheet(nav_btn_style)
        self.forward_btn.setFixedWidth(40)
        self.forward_btn.clicked.connect(self.nav_forward_clicked.emit)
        layout.addWidget(self.forward_btn)
        
        # Action buttons configuration: (Label, Signal Name)
        actions = [
            ("+ New", "new"),
            ("✂ Cut", "cut"),
            ("📋 Copy", "copy"),
            ("📄 Paste", "paste"),
            ("✏ Rename", "rename"),
            ("⤴ Share", "share"),
            ("🗑 Delete", "delete")
        ]

        self.action_buttons = {} # NEW: Store buttons to translate them later
        
        for text, action_name in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda checked, a=action_name: self.action_clicked.emit(a))
            layout.addWidget(btn)

            self.action_buttons[action_name] = (text, btn)
        
        layout.addStretch()
        
        # Smart Organise button
        if show_smart_button:
            self.smart_base_text = button_text # NEW: Store base text
            self.smart_btn = QPushButton(f"✏ {button_text}") # NEW: Use self.smart_btn
            self.smart_btn.setStyleSheet("""
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
            self.smart_btn.clicked.connect(self.smart_organise_clicked.emit)
            layout.addWidget(self.smart_btn)

        self.setLayout(layout)
        
    def update_translations(self, lang_code):
        # 1. Translate main action buttons
        for action_name, (original_text, btn) in self.action_buttons.items():
            # Split the icon (e.g., "➕") from the word (e.g., "New")
            parts = original_text.split(" ", 1)
            if len(parts) == 2:
                icon, word = parts
                translated_word = translate_text(word, lang_code)
                btn.setText(f"{icon} {translated_word}")

        # 2. Translate Smart Organise button
        if hasattr(self, 'smart_btn'):
            translated_smart = translate_text(self.smart_base_text, lang_code)
            self.smart_btn.setText(f"✏ {translated_smart}")