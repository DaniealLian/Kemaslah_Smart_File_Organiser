from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtCore import QMargins  # Ensure this is imported

class PieChartWidget(QWidget):
    def __init__(self, title, data):
        super().__init__()
        # 1. Force a large height so charts are identical and big
        self.setMinimumHeight(500)
        self.init_ui(title, data)
        
    def init_ui(self, title, data):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create pie chart
        series = QPieSeries()
        # 2. Reduce pie size slightly (0.7) to give labels more room to float outside
        series.setPieSize(0.7) 
        
        colors = ["#D946EF", "#06B6D4", "#22D3EE", "#8B5CF6"]
        
        for i, (label, value) in enumerate(data):
            slice_item = series.append(label, value)
            slice_item.setColor(QColor(colors[i % len(colors)]))

            # 3. Label Settings
            slice_item.setLabelVisible(True)
            slice_item.setLabel(f"{int(value)}%")
            slice_item.setLabelBrush(QColor("white"))
            
            # Make text bold/larger
            f = QFont("Arial", 10)
            f.setBold(True)
            slice_item.setLabelFont(f)
            
            # Force labels outside
            slice_item.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#2D3748"))
        
        # 4. Remove whitespace margins
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setVisible(False)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background-color: transparent; border: none;")
        chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout.addWidget(chart_view)
        
        # Legend
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(8)
        
        for i, (label, _) in enumerate(data):
            legend_item = QHBoxLayout()
            
            color_box = QLabel()
            color_box.setFixedSize(12, 12)
            color_box.setStyleSheet(f"background-color: {colors[i % len(colors)]}; border-radius: 2px;")
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #C0C0C0; font-size: 11px;")
            
            legend_item.addWidget(color_box)
            legend_item.addWidget(label_widget)
            legend_item.addStretch()
            
            legend_layout.addLayout(legend_item)
        
        layout.addLayout(legend_layout)
        self.setLayout(layout)