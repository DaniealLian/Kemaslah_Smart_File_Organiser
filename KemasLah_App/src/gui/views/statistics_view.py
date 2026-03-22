import os
import json # NEW: For reading the AI report card
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                             QScrollArea, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView) # NEW: Added table components
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QColor, QPainter

class StatisticsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Title
        self.title_label = QLabel("Storage Statistics")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.main_layout.addWidget(self.title_label)

        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setSpacing(30)

        # --- EXISTING CHARTS SECTION ---
        charts_container = QWidget()
        charts_layout = QHBoxLayout(charts_container)
        charts_layout.setSpacing(20)

        # 1. File Type Distribution (Pie Chart)
        self.pie_chart_view = self.create_pie_chart()
        charts_layout.addWidget(self.pie_chart_view, 1)

        # 2. Storage Usage (Bar Chart)
        self.bar_chart_view = self.create_bar_chart()
        charts_layout.addWidget(self.bar_chart_view, 1)

        self.content_layout.addWidget(charts_container)

        # --- NEW: AI PERFORMANCE DASHBOARD ---
        self.setup_ai_stats()

        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

    def setup_ai_stats(self):
        """Creates the professional AI metrics section"""
        ai_container = QFrame()
        ai_container.setObjectName("AIContainer")
        ai_container.setStyleSheet("""
            QFrame#AIContainer {
                background-color: #2D3748;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        ai_layout = QVBoxLayout(ai_container)

        # Dashboard Header
        self.ai_title = QLabel("🤖 AI Model Performance (TF-IDF + SVM)")
        self.ai_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #63B3ED; margin-bottom: 10px;")
        ai_layout.addWidget(self.ai_title)

        # Information Label
        self.ai_info = QLabel("Metrics derived from the BBC News Training Dataset.")
        self.ai_info.setStyleSheet("color: #A0AEC0; font-size: 12px; margin-bottom: 10px;")
        ai_layout.addWidget(self.ai_info)

        # The Performance Table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(4)
        self.metrics_table.setHorizontalHeaderLabels(["Folder Category", "Precision", "Recall", "F1-Score"])
        
        # Professional Styling for Table
        self.metrics_table.setStyleSheet("""
            QTableWidget {
                background-color: #1A202C;
                color: #E2E8F0;
                gridline-color: #4A5568;
                border: none;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #4A5568;
                color: white;
                padding: 5px;
                border: 1px solid #2D3748;
                font-weight: bold;
            }
        """)
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setFixedHeight(250)

        ai_layout.addWidget(self.metrics_table)
        self.content_layout.addWidget(ai_container)

        # Load the data immediately
        self.load_ai_metrics()

    def load_ai_metrics(self):
        """Reads the ai_metrics.json file and populates the table"""
        metrics_path = 'AI/ai_metrics.json'  # UPDATED PATH: Added 'AI/' prefix
        
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    data = json.load(f)
                
                # Filter out the summary keys (accuracy, macro avg, weighted avg)
                categories = [k for k in data.keys() if k not in ['accuracy', 'macro avg', 'weighted avg']]
                
                self.metrics_table.setRowCount(len(categories))
                
                for i, cat in enumerate(categories):
                    # Set Category Name
                    self.metrics_table.setItem(i, 0, QTableWidgetItem(cat))
                    
                    # Set Metrics (Formatted to 2 decimal places)
                    prec = data[cat]['precision']
                    rec = data[cat]['recall']
                    f1 = data[cat]['f1-score']
                    
                    self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{prec:.2f}"))
                    self.metrics_table.setItem(i, 2, QTableWidgetItem(f"{rec:.2f}"))
                    self.metrics_table.setItem(i, 3, QTableWidgetItem(f"{f1:.2f}"))
                    
                    # Align text to center
                    for col in range(4):
                        self.metrics_table.item(i, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            except Exception as e:
                print(f"Error loading AI metrics: {e}")
                self.ai_info.setText("Error loading performance data.")
        else:
            self.ai_info.setText("Status: No trained model found. Please run 'train_ai.py' to generate metrics.")

    # --- START OF ORIGINAL CHART CODE ---
    def create_pie_chart(self):
        series = QPieSeries()
        series.append("Documents", 45)
        series.append("Images", 25)
        series.append("Videos", 15)
        series.append("Music", 10)
        series.append("Others", 5)

        # Styling
        colors = ["#4299E1", "#48BB78", "#F6E05E", "#ED64A6", "#A0AEC0"]
        for i, slice in enumerate(series.slices()):
            slice.setBrush(QColor(colors[i % len(colors)]))
            slice.setLabelVisible(True)
            slice.setLabel(f"{slice.label()} ({slice.percentage()*100:.0f}%)")
            slice.hovered.connect(lambda state, s=slice: self.on_slice_hovered(state, s))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("File Type Distribution")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(QColor("white"))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(QColor("white"))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background-color: #2D3748; border-radius: 12px; padding: 10px;")
        chart_view.setMinimumHeight(400)
        return chart_view

    def create_bar_chart(self):
        set0 = QBarSet("Usage (GB)")
        set0.append([12, 18, 8, 25, 14, 20])
        set0.setBrush(QColor("#63B3ED"))

        series = QBarSeries()
        series.append(set0)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Storage Usage by Category")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(QColor("white"))

        categories = ["Work", "Personal", "Projects", "Media", "Archive", "System"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor("white"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 30)
        axis_y.setLabelsColor(QColor("white"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(QColor("white"))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background-color: #2D3748; border-radius: 12px; padding: 10px;")
        chart_view.setMinimumHeight(400)
        return chart_view

    def on_slice_hovered(self, state, slice):
        if state:
            slice.setExploded(True)
            slice.setLabelVisible(True)
        else:
            slice.setExploded(False)

    def update_translations(self, lang_code):
        """Updates UI text based on language"""
        from src.utils.translator import translate_text
        
        self.title_label.setText(translate_text("Storage Statistics", lang_code))
        self.ai_title.setText(translate_text("AI Model Performance (TF-IDF + SVM)", lang_code))
        
        # Update chart titles if needed
        self.pie_chart_view.chart().setTitle(translate_text("File Type Distribution", lang_code))
        self.bar_chart_view.chart().setTitle(translate_text("Storage Usage by Category", lang_code))