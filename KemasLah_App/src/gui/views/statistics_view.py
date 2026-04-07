import os
import json
import shutil
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                             QScrollArea, QFrame, QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtGui import QColor, QPainter

# ─── File Scanning Helpers ────────────────────────────────────────────────────

def scan_pc_files():
    TEXT_EXTS    = {'.doc','.docx','.odt','.rtf','.txt','.pdf','.md','.csv',
                    '.xlsx','.xls','.pptx','.ppt','.json','.xml','.yaml','.yml','.log','.ini','.toml'}
    IMAGE_VIDEO  = {'.jpg','.jpeg','.png','.gif','.bmp','.webp','.tiff','.svg','.ico',
                    '.mp4','.avi','.mov','.mkv','.wmv','.flv','.webm','.mp3','.wav','.flac','.aac','.ogg','.wma'}
    DEV_CODE     = {'.html','.htm','.css','.js','.ts','.py','.java','.c','.cpp',
                    '.cs','.php','.rb','.go','.rs','.swift','.kt','.sh','.bat'}
    ARCHIVE_INST = {'.zip','.rar','.7z','.tar','.gz','.exe','.msi','.dmg','.iso','.dll','.bin'}

    counts = {"Text-Based files": 0, "Image & Video files": 0,
              "Developer & Code files": 0, "Archives & Installers": 0}
    total_size = 0
    SKIP_DIRS = {'Windows','Program Files','Program Files (x86)',
                 'ProgramData','Recovery','System Volume Information'}

    roots = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    if not roots:
        roots = [os.path.expanduser("~")]

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if not d.startswith('$') and d not in SKIP_DIRS]
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                try:
                    total_size += os.path.getsize(os.path.join(dirpath, fname))
                except OSError:
                    pass
                if ext in TEXT_EXTS:        counts["Text-Based files"] += 1
                elif ext in IMAGE_VIDEO:    counts["Image & Video files"] += 1
                elif ext in DEV_CODE:       counts["Developer & Code files"] += 1
                elif ext in ARCHIVE_INST:   counts["Archives & Installers"] += 1
    return counts, total_size

def scan_location_files():
    locs = {
        "Documents Folder": os.path.expanduser("~/Documents"),
        "Pictures Folder":  os.path.expanduser("~/Pictures"),
        "Video Folder":     os.path.expanduser("~/Videos"),
    }
    counts = {}
    for label, path in locs.items():
        total = 0
        if os.path.exists(path):
            for _, _, files in os.walk(path):
                total += len(files)
        counts[label] = max(total, 0)
    return counts

def get_total_disk_info():
    try:
        u = shutil.disk_usage("C:\\")
        return u.used, u.total
    except Exception:
        try:
            u = shutil.disk_usage(os.path.expanduser("~"))
            return u.used, u.total
        except Exception:
            return 20*(1024**3), 125*(1024**3)

def get_archivable_size():
    total = 0
    cutoff = datetime.now() - timedelta(days=180)
    SKIP_DIRS = {'Windows','Program Files','Program Files (x86)',
                 'ProgramData','Recovery','System Volume Information'}
    roots = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    if not roots:
        roots = [os.path.expanduser("~")]
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if not d.startswith('$') and d not in SKIP_DIRS]
            for fname in filenames:
                fp = os.path.join(dirpath, fname)
                try:
                    if datetime.fromtimestamp(os.path.getmtime(fp)) < cutoff:
                        total += os.path.getsize(fp)
                except OSError:
                    pass
    return total

# ─── Feature Usage Tracking ───────────────────────────────────────────────────

def record_feature_use(feature: str):
    """Call record_feature_use('organise') or ('archive') when each feature is triggered."""
    s = QSettings("Kemaslah", "SmartFileManager")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if feature == "organise":
        s.setValue("feature/organise_count", s.value("feature/organise_count", 0, int) + 1)
        s.setValue("feature/organise_last", now)
    elif feature == "archive":
        s.setValue("feature/archive_count", s.value("feature/archive_count", 0, int) + 1)
        s.setValue("feature/archive_last", now)

def get_feature_stats():
    s = QSettings("Kemaslah", "SmartFileManager")
    def fmt(val):
        if not val: return "Never"
        try:
            delta = datetime.now() - datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            if delta.days == 0: return "Today"
            if delta.days == 1: return "Yesterday"
            return f"{delta.days} days ago"
        except Exception:
            return str(val)
    return {
        "organise_count": s.value("feature/organise_count", 0, int),
        "organise_last":  fmt(s.value("feature/organise_last",  "", str)),
        "archive_count":  s.value("feature/archive_count",  0, int),
        "archive_last":   fmt(s.value("feature/archive_last",   "", str)),
    }

# ─── Reusable Widgets ─────────────────────────────────────────────────────────

class StorageBar(QWidget):
    def __init__(self, used_gb, total_gb, bottom_label="", color="#3B82F6"):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.addStretch()
        total_lbl = QLabel(f"{total_gb:.0f}GB")
        total_lbl.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        top.addWidget(total_lbl)
        layout.addLayout(top)

        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(max(int(total_gb), 1))
        bar.setValue(int(used_gb))
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #1F2937; border-radius: 6px; border: none; }}
            QProgressBar::chunk {{ background-color: {color}; border-radius: 6px; }}
        """)
        layout.addWidget(bar)

        bot = QLabel(f"{used_gb:.0f}GB {bottom_label}".strip())
        bot.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(bot)


class FeatureUsageBlock(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("Application's Feature Usage")
        header.setStyleSheet("color: #6B7280; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(header)

        self.organise_title = QLabel("Smart Organise")
        self.organise_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-top: 6px;")
        layout.addWidget(self.organise_title)

        self.organise_info = QLabel("Number of usage: 0     Last used: Never")
        self.organise_info.setStyleSheet("color: #9CA3AF; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(self.organise_info)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #1F2937;")
        layout.addWidget(div)

        self.archive_title = QLabel("Smart Archive")
        self.archive_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-top: 12px;")
        layout.addWidget(self.archive_title)

        self.archive_info = QLabel("Number of usage: 0     Last used: Never")
        self.archive_info.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(self.archive_info)

    def update_stats(self, stats):
        self.organise_info.setText(
            f"Number of usage: {stats['organise_count']}     Last used: {stats['organise_last']}")
        self.archive_info.setText(
            f"Number of usage: {stats['archive_count']}     Last used: {stats['archive_last']}")


# ─── Main Statistics View ─────────────────────────────────────────────────────

TYPE_COLORS = ["#D946EF", "#38BDF8", "#34D399", "#818CF8"]
LOC_COLORS  = ["#D946EF", "#38BDF8", "#34D399"]

TYPE_SUBTITLES = {
    "Text-Based files":       ".doc, .docx, .odt, .rtf, .txt, etc...",
    "Image & Video files":    ".mp4, .mov, .avi, .mkv, etc...",
    "Developer & Code files": ".html, .css, .js, .py, .java, etc...",
    "Archives & Installers":  ".zip, .rar, .7z, .exe, .msi, etc...",
}

class StatisticsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._built = False
        self.setStyleSheet("background-color: #111827;")

    def showEvent(self, event):
        super().showEvent(event)
        if not self._built:
            self._built = True
            self._build_ui()
        else:
            self._refresh()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #111827; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        root_widget = QWidget()
        root_widget.setStyleSheet("background-color: #111827;")
        root = QHBoxLayout(root_widget)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(28)

        # ── LEFT: Two pie charts ──────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)

        type_title = QLabel("Distribution of File Types within this PC")
        type_title.setStyleSheet("font-size: 13px; font-weight: bold; color: white; text-decoration: underline;")
        left.addWidget(type_title)

        self.pie_type_view = self._empty_pie_view()
        self.pie_type_view.setMinimumHeight(300)
        left.addWidget(self.pie_type_view)

        loc_title = QLabel("Distribution of Files in a Location within this PC")
        loc_title.setStyleSheet("font-size: 13px; font-weight: bold; color: white; text-decoration: underline; margin-top: 12px;")
        left.addWidget(loc_title)

        self.pie_loc_view = self._empty_pie_view()
        self.pie_loc_view.setMinimumHeight(280)
        left.addWidget(self.pie_loc_view)
        left.addStretch()

        left_w = QWidget(); left_w.setLayout(left)
        left_w.setStyleSheet("background-color: transparent;")

        # ── RIGHT: Storage + feature usage ───────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        total_title = QLabel("Total File Size")
        total_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        right.addWidget(total_title)

        self.total_bar_container = QVBoxLayout()
        self.total_bar_container.setContentsMargins(0,0,0,0)
        used, total = get_total_disk_info()
        self.total_bar = StorageBar(used/(1024**3), total/(1024**3), "used", "#3B82F6")
        self.total_bar_container.addWidget(self.total_bar)
        tw = QWidget(); tw.setLayout(self.total_bar_container)
        tw.setStyleSheet("background: transparent;")
        right.addWidget(tw)

        arch_title = QLabel("Archivable Files")
        arch_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; margin-top: 14px;")
        right.addWidget(arch_title)

        self.arch_bar_container = QVBoxLayout()
        self.arch_bar_container.setContentsMargins(0,0,0,0)
        self.arch_bar = StorageBar(0, total/(1024**3), "Archivable Files", "#3B82F6")
        self.arch_bar_container.addWidget(self.arch_bar)
        aw = QWidget(); aw.setLayout(self.arch_bar_container)
        aw.setStyleSheet("background: transparent;")
        right.addWidget(aw)

        self.feature_block = FeatureUsageBlock()
        right.addWidget(self.feature_block)
        right.addStretch()

        right_w = QWidget(); right_w.setLayout(right)
        right_w.setStyleSheet("background-color: transparent;")
        right_w.setFixedWidth(380)

        root.addWidget(left_w, 3)
        root.addWidget(right_w, 2)

        scroll.setWidget(root_widget)
        outer.addWidget(scroll)

        self._refresh()

    # ── Data Refresh ──────────────────────────────────────────────────────────

    def _refresh(self):
        self._refresh_pie_type()
        self._refresh_pie_loc()
        self._refresh_storage()
        self._refresh_features()

    def _refresh_pie_type(self):
        counts, _ = scan_pc_files()
        labels = list(counts.keys())
        values = list(counts.values())
        self._fill_pie(self.pie_type_view, labels, values, TYPE_COLORS, TYPE_SUBTITLES)

    def _refresh_pie_loc(self):
        counts = scan_location_files()
        labels = list(counts.keys())
        values = list(counts.values())
        self._fill_pie(self.pie_loc_view, labels, values, LOC_COLORS, {})

    def _refresh_storage(self):
        used, total = get_total_disk_info()
        used_gb  = used  / (1024**3)
        total_gb = total / (1024**3)
        self._swap_bar(self.total_bar_container, "total_bar",
                       used_gb, total_gb, "used", "#3B82F6")

        arch_bytes = get_archivable_size()
        arch_gb = arch_bytes / (1024**3)
        self._swap_bar(self.arch_bar_container, "arch_bar",
                       arch_gb, total_gb, "Archivable Files", "#3B82F6")

    def _swap_bar(self, container_layout, attr, used_gb, total_gb, label, color):
        old = getattr(self, attr)
        if old:
            old.setParent(None)
        new_bar = StorageBar(used_gb, total_gb, label, color)
        container_layout.addWidget(new_bar)
        setattr(self, attr, new_bar)

    def _refresh_features(self):
        self.feature_block.update_stats(get_feature_stats())

    # ── Pie Chart Helpers ─────────────────────────────────────────────────────

    def _empty_pie_view(self):
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(False)
        chart.setContentsMargins(0, 0, 0, 0)
        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet("background: transparent; border: none;")
        return view

    def _fill_pie(self, view, labels, values, colors, subtitles):
        series = QPieSeries()
        total = sum(values) or 1

        for i, (lbl, val) in enumerate(zip(labels, values)):
            pct = val / total * 100
            sl = series.append(f"{pct:.0f}%", val if val > 0 else 0.01)
            sl.setBrush(QColor(colors[i % len(colors)]))
            sl.setLabelVisible(True)
            try:
                sl.setLabelPosition(QPieSlice.LabelPosition.LabelInsideHorizontal)
            except AttributeError:
                sl.setLabelPosition(2)  # 2 = LabelInsideHorizontal fallback
            sl.setLabelColor(QColor("white"))
            sl.setLabelFont(self._bold_font(10))
            sl.hovered.connect(lambda state, s=sl: s.setExploded(state))

        chart = view.chart()
        chart.removeAllSeries()
        chart.addSeries(series)

        # Custom legend
        legend = chart.legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignmentFlag.AlignRight)
        legend.setLabelColor(QColor("white"))
        legend.setFont(self._font(11))

        # Update legend marker labels to include subtitle
        for i, marker in enumerate(legend.markers(series)):
            lbl = labels[i] if i < len(labels) else ""
            sub = subtitles.get(lbl, "")
            marker.setLabel(f"{lbl}\n{sub}" if sub else lbl)
            marker.setFont(self._font(10))

    def _font(self, size):
        f = self.font()
        f.setPointSize(size)
        return f

    def _bold_font(self, size):
        f = self._font(size)
        f.setBold(True)
        return f

    # ── Translation ───────────────────────────────────────────────────────────

    def update_translations(self, lang_code):
        pass