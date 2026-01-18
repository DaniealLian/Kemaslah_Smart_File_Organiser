import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class KemasLahApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.setWindowTitle("KemasLah - Intelligent File Sorter")
        self.setGeometry(100, 100, 1080, 720) # HD Resolution

        # 2. Basic Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # 3. Add a placeholder label
        self.label = QLabel("Welcome to KemasLah\nSystem Status: Ready")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        self.layout.addWidget(self.label)

if __name__ == "__main__":
    # 4. Launch the App
    app = QApplication(sys.argv)
    window = KemasLahApp()
    window.show()
    sys.exit(app.exec())