from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox
from ..widgets.topbar import TopBar
from ..widgets.actionbar import ActionBar
from ..widgets.file_table import FileTableWidget

class ArchiveView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            layout.addWidget(TopBar())
            layout.addWidget(ActionBar(True, "Smart Archive"))
            
            # Label checkbox area
            label_widget = QWidget()
            label_layout = QHBoxLayout()
            label_layout.setContentsMargins(20, 10, 20, 0)
            label_cb = QCheckBox("Label")
            # ... (keep your label style) ...
            label_layout.addWidget(label_cb)
            label_layout.addStretch()
            label_widget.setLayout(label_layout)
            layout.addWidget(label_widget)
            
            # --- FIX STARTS HERE ---
            # 1. Initialize the table WITHOUT arguments
            self.file_table = FileTableWidget()
            
            # 2. Add it to layout
            layout.addWidget(self.file_table)
            
            # 3. (Optional) If you want to show specific archive files here, 
            # you will need to add a new method to FileTableWidget to accept manual data
            # or load a specific folder like:
            # self.file_table.load_files("C:/Users/User/Documents/Archive") 
            
            self.setLayout(layout)