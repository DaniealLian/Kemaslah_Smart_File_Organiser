from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

class ActionBar(QWidget):
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
        pass