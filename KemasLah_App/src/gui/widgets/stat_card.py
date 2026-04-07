from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from auth.authentication_page import translate_text # NEW: Import translation

class StatCard(QWidget):
    def __init__(self, title, value, total, color="#2563EB"):
        super().__init__()
        self.base_title = title       # NEW: Store original text
        self.current_value = value    # NEW: Store values to rebuild string
        self.init_ui(title, value, total, color)
        
    def init_ui(self, title, value, total, color):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        self.title_label = QLabel(title) # CHANGED: Added self.
        self.title_label.setStyleSheet("color: #C0C0C0; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Progress bar
        progress_widget = QWidget()
        progress_widget.setFixedHeight(8)
        progress_widget.setStyleSheet("""
            QWidget {
                background-color: #2D3748;
                border-radius: 4px;
            }
        """)
        
        progress_fill = QWidget(progress_widget)
        progress_width = int((value / total) * progress_widget.width()) if total > 0 else 0
        progress_fill.setGeometry(0, 0, progress_width, 8)
        progress_fill.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(progress_widget)
        
        # Value labels
        value_layout = QHBoxLayout()
        self.value_label = QLabel(f"{value}GB used") # CHANGED: Added self.
        self.value_label.setStyleSheet("color: #E0E0E0; font-size: 12px;")
        
        self.total_label = QLabel(f"{total}GB") # CHANGED: Added self.
        self.total_label.setStyleSheet("color: #888888; font-size: 12px;")
        
        value_layout.addWidget(self.value_label)
        value_layout.addStretch()
        value_layout.addWidget(self.total_label)
        layout.addLayout(value_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            StatCard {
                background-color: #2D3748;
                border-radius: 8px;
            }
        """)

    # --- NEW: Translation Method ---
    def update_translations(self, lang_code):
        self.title_label.setText(translate_text(self.base_title, lang_code))
        translated_used = translate_text("GB used", lang_code)
        self.value_label.setText(f"{self.current_value}{translated_used}")