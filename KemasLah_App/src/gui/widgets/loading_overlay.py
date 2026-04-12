from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QSizePolicy
from PyQt6.QtCore import Qt


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 105);")
        self.hide()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setObjectName("loadingCard")
        self.card.setMinimumWidth(360)
        self.card.setMaximumWidth(420)
        self.card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.card.setStyleSheet("""
            QFrame#loadingCard {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 26, 30, 26)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel("⏳")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            background-color: transparent;
            margin-bottom: 2px;
        """)

        self.label = QLabel("Loading...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            color: white;
            font-size: 17px;
            font-weight: 700;
            background-color: transparent;
        """)

        self.sub_label = QLabel("Please wait a moment")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setWordWrap(True)
        self.sub_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 12px;
            background-color: transparent;
        """)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(240)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }
        """)

        card_layout.addWidget(self.icon_label)
        card_layout.addWidget(self.label)
        card_layout.addWidget(self.sub_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)

        root_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_message(self, message="Loading...", sub_message="Please wait a moment", icon="⏳"):
        self.label.setText(message)
        self.sub_label.setText(sub_message)
        self.icon_label.setText(icon)

        if self.parent():
            self.resize(self.parent().size())

        self.show()
        self.raise_()

    def update_message(self, message, sub_message="Please wait a moment", icon=None):
        self.label.setText(message)
        self.sub_label.setText(sub_message)
        if icon is not None:
            self.icon_label.setText(icon)

    def hide_overlay(self):
        self.hide()