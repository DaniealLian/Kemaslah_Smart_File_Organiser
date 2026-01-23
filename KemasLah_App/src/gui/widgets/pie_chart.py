from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QColor, QPainter

class PieChartWidget(QWidget):
    def __init__(self, title, data):
        super().__init__()
        self.init_ui(title, data)
        
    def init_ui(self, title, data):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create pie chart
        series = QPieSeries()
        colors = ["#D946EF", "#06B6D4", "#22D3EE", "#8B5CF6"]
        
        for i, (label, value) in enumerate(data):
            slice = series.append(label, value)
            slice.setColor(QColor(colors[i % len(colors)]))
            slice.setLabelVisible(True)
            slice.setLabel(f"{int(value)}%")
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#2D3748"))
        chart.legend().setVisible(False)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background-color: transparent; border: none;")
        
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
        pass