import sys
import threading
import logging
import os 
import json 
import joblib 
import shutil 
import PyPDF2 
import pandas as pd 
import docx 
import numpy as np 
import re 

# --- YOUR REQUIRED PROJECT ALGORITHMS ---
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.svm import SVC                                 
from sklearn.ensemble import RandomForestClassifier         
from sklearn.cluster import KMeans 
from sklearn.metrics.pairwise import cosine_similarity 
from sklearn.metrics import precision_score, recall_score, accuracy_score 
from sklearn.model_selection import train_test_split
# ----------------------------------------

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QStackedWidget, QVBoxLayout, QMessageBox, QDialog, 
                             QRadioButton, QButtonGroup, QPushButton, QLabel,
                             QProgressDialog, QTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtCharts import QChart, QChartView, QPieSeries

# Import authentication system
from auth.authentication_page import MainWindow as AuthWindow
from auth.server import app as flask_app
from auth.database import create_db

# Import your existing GUI components
from src.gui.widgets.sidebar import Sidebar
from src.gui.widgets.topbar import TopBar
from src.gui.widgets.actionbar import ActionBar
from src.gui.views.home_view import HomeView
from src.gui.views.file_browser_view import FileBrowserView
from src.gui.views.archive_view import ArchiveView
from src.gui.views.statistics_view import StatisticsView
from src.gui.views.settings_view import SettingsView

# --- Import the Share Dialog and File Sharing View ---
from src.gui.views.share_dialog import ShareFileDialog
from src.gui.views.file_sharing_view import FileSharingView
# ----------------------------------------------------------

#import to add cnn model
from pathlib import Path
from src.inference.classifier_worker import (
    CNNSearchWorker, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
)

CNN_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models", "trained", "best_model.pth"
)
 
# Convenience sets — used throughout handle_smart_organise
_MEDIA_EXTS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS   # {'.jpg', '.mp4', ...}


class SmartFileManager(QMainWindow):
    """Enterprise File Manager: Absolute Keyword Search & Anti-Silent-Fail Logging"""
    logout_requested = pyqtSignal()
    
    def __init__(self, user_data=None, auth_window=None):  
        super().__init__()
        self.user_data = user_data or {"username": "Guest", "email": "guest@local", "initials": "G"}
        self.auth_window = auth_window  
        self.setWindowTitle("Kemaslah File Manager")
        self.resize(1200, 800)
        self.settings_overlay = None
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.current_search_query = ""
        self._image_classifier  = None   # lazy-loaded ImageClassifier (CNN)
        self._cnn_search_worker = None   # background CNNSearchWorker thread
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = Sidebar(user_data=self.user_data)
        self.sidebar.navigation_changed.connect(self.switch_view)
        self.sidebar.logout_requested.connect(self.handle_logout)
        main_layout.addWidget(self.sidebar)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.top_bar = TopBar()
        self.top_bar.path_changed.connect(self.on_topbar_nav)
        self.top_bar.search_query_changed.connect(self.handle_search)
        right_layout.addWidget(self.top_bar)

        self.stack = QStackedWidget()
        self.home_view = HomeView()
        self.files_view = FileBrowserView()
        self.archive_view = ArchiveView()
        self.statistics_view = StatisticsView()
        self.sharing_view = FileSharingView(self.user_data.get("email")) 
        
        self.action_bar = ActionBar(True, "Smart Organise")
        self.action_bar.action_clicked.connect(self.handle_action_bar)
        self.action_bar.smart_organise_clicked.connect(self.handle_smart_organise)
        
        self.action_bar.nav_back_clicked.connect(self.files_view.go_back)
        self.action_bar.nav_forward_clicked.connect(self.files_view.go_forward)

        right_layout.addWidget(self.action_bar)
        
        self.files_view.path_changed.connect(self.top_bar.update_breadcrumbs)
        self.home_view.folder_opened.connect(self.on_home_folder_opened)
        self.files_view.file_table.share_requested.connect(self.open_share_dialog) 
        
        self.stack.addWidget(self.home_view)        
        self.stack.addWidget(self.files_view)       
        self.stack.addWidget(self.archive_view)     
        self.stack.addWidget(self.statistics_view)  
        self.stack.addWidget(self.sharing_view)     
        
        right_layout.addWidget(self.stack)
        main_layout.addWidget(right_panel)
        self.switch_view("home")

    def open_share_dialog(self, file_path):
        is_guest = (self.user_data.get("username") == "Guest User")
        dialog = ShareFileDialog(file_path=file_path, current_user_email=self.user_data.get("email"), is_guest=is_guest, parent=self)
        dialog.exec() 

    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self.logout_requested.emit()

    def handle_action_bar(self, action_name):
        current_widget = self.stack.currentWidget()
        if current_widget == self.files_view:
            self.files_view.file_table.perform_action(action_name.lower()) 

    # -------------------------------------------------------------------------
    # --- ABSOLUTE SEARCH ENHANCEMENTS: Bulletproof String Matching ---
    # -------------------------------------------------------------------------
    def handle_search(self, query):
        self.current_search_query = query
        if self.stack.currentWidget() != self.files_view: self.switch_view("files")
        self.files_view.file_table.filter_files(query)
        self.search_timer.start(800) 

    def perform_search(self):
        query = self.current_search_query.strip()
        if len(query) < 3: return 
        self.perform_ai_deep_search(query)

    def perform_ai_deep_search(self, ai_query):
        """
        Deep content search — text documents (TF-IDF) + images/videos (CNN).
        """
        query_lower  = ai_query.lower()
        current_path = self.files_view.current_path
        if not os.path.exists(current_path):
            return
    
        all_files = [
            os.path.join(current_path, f)
            for f in os.listdir(current_path)
            if os.path.isfile(os.path.join(current_path, f))
        ]
        if not all_files:
            QMessageBox.information(
                self, "Content Scanner",
                f"No files inside '{os.path.basename(current_path)}' to scan.\n\n"
                "Navigate to the folder that contains your file.")
            return
    
        text_files  = [f for f in all_files
                    if Path(f).suffix.lower() not in _MEDIA_EXTS]
        media_files = [f for f in all_files
                    if Path(f).suffix.lower() in _MEDIA_EXTS]
    
        # ── PART A: Text document search (your original logic, unchanged) ─────────
        if text_files:
            progress = QProgressDialog(
                f"Deep scanning {len(text_files)} document(s)…",
                "Cancel", 0, len(text_files), self)
            progress.setMinimumDuration(500)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
    
            def quick_content_extract(filepath):
                ext      = filepath.lower().split('.')[-1] if '.' in filepath else ''
                raw_text = ""
                try:
                    if ext == 'pdf':
                        with open(filepath, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for i in range(min(5, len(reader.pages))):
                                pt = reader.pages[i].extract_text()
                                if pt:
                                    raw_text += pt + " "
                    elif ext == 'docx':
                        doc = docx.Document(filepath)
                        for para in doc.paragraphs[:50]:
                            raw_text += para.text + " "
                    elif ext in ['txt', 'md', 'csv', 'py', 'json']:
                        with open(filepath, 'r', encoding='utf-8',
                                errors='ignore') as f:
                            raw_text = f.read(10000)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                return raw_text.lower()
    
            docs, valid_files = [], []
            for i, fp in enumerate(text_files):
                if progress.wasCanceled():
                    break
                content = quick_content_extract(fp)
                if content.strip():
                    docs.append(content); valid_files.append(fp)
                progress.setValue(i + 1); QApplication.processEvents()
            progress.close()
    
            if valid_files:
                try:
                    found = []
                    for idx, content in enumerate(docs):
                        if query_lower in content:
                            found.append((idx, 1.0, "Exact Keyword Match"))
    
                    if not found:
                        vec_s    = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
                        tfidf_m  = vec_s.fit_transform([query_lower] + docs)
                        cos_sim  = cosine_similarity(
                            tfidf_m[0:1], tfidf_m[1:]).flatten()
                        for idx in cos_sim.argsort()[-5:][::-1]:
                            if cos_sim[idx] > 0.001:
                                found.append((idx, cos_sim[idx], "Semantic AI Match"))
    
                    if found:
                        result_msg = f"🔍 Document Matches for: '{ai_query}'\n\n"
                        for idx, score, match_type in found:
                            fn  = os.path.basename(valid_files[idx])
                            sc  = ("100% (Exact)" if match_type == "Exact Keyword Match"
                                else f"{score:.1%}")
                            result_msg += (f"📄 {fn}\n"
                                        f"   • Type  : {match_type}\n"
                                        f"   • Score : {sc}\n\n")
                        dialog = QDialog(self)
                        dialog.setWindowTitle("Document Search Results")
                        dialog.resize(600, 400)
                        lay = QVBoxLayout(dialog)
                        lay.addWidget(QLabel(
                            f"<b>Top document matches for '{ai_query}':</b>"))
                        te = QTextEdit(dialog)
                        te.setReadOnly(True); te.setText(result_msg)
                        lay.addWidget(te)
                        btn = QPushButton("Close"); btn.clicked.connect(dialog.accept)
                        lay.addWidget(btn); dialog.exec()
    
                except Exception as e:
                    if "empty vocabulary" in str(e).lower():
                        QMessageBox.warning(self, "Search Alert",
                                            "Query contains invalid characters.")
                    else:
                        QMessageBox.critical(self, "Search Error", str(e))
                        print(f"Deep Search Error: {e}")
    
        # ── PART B: CNN image/video search (NEW — background thread) ─────────────
        if media_files:
            if not os.path.exists(CNN_MODEL_PATH):
                print("[CNN Search] best_model.pth not found — skipping image search.")
                return
    
            # Stop any previous search still running
            if self._cnn_search_worker and self._cnn_search_worker.isRunning():
                self._cnn_search_worker.stop()
                self._cnn_search_worker.wait()
    
            QMessageBox.information(
                self, "Image Search Started",
                f"🖼️  Also scanning {len(media_files)} image/video file(s) by "
                f"visual content.\n\nMatching results will appear in the "
                f"file list below as they are found."
            )
    
            self._cnn_search_worker = CNNSearchWorker(
                query      = ai_query,
                search_path= current_path,
                model_path = CNN_MODEL_PATH,
            )
            self._cnn_search_worker.match_found.connect(self._on_cnn_image_match)
            self._cnn_search_worker.search_finished.connect(self._on_cnn_search_done)
            self._cnn_search_worker.error_occurred.connect(self._on_cnn_search_error)
            self._cnn_search_worker.start()

    # -------------------------------------------------------------------------
    # --- CORE AI LOGIC: Sorting and Organization ---
    # -------------------------------------------------------------------------
    def handle_smart_organise(self):
        current_widget = self.stack.currentWidget()
        if current_widget != self.files_view:
            return
    
        selected_paths = self.files_view.file_table.get_selected_files()
        if not selected_paths:
            QMessageBox.warning(self, "No Selection",
                                "Please select folders or files to organize.")
            return
    
        # ── Split selection by type ───────────────────────────────────────────────
        folders_selected = [p for p in selected_paths if os.path.isdir(p)]
        files_selected   = [p for p in selected_paths if os.path.isfile(p)]
    
        image_files = [f for f in files_selected
                    if Path(f).suffix.lower() in IMAGE_EXTENSIONS]
        video_files = [f for f in files_selected
                    if Path(f).suffix.lower() in VIDEO_EXTENSIONS]
        text_files  = [f for f in files_selected
                    if f not in image_files and f not in video_files]
    
        move_history      = []
        results_message   = "🤖 AI Smart Organise Complete!\n\n"
        metrics_message   = ""
        current_view_path = self.files_view.current_path
    
        # ── Text-content extractor (unchanged from your original) ─────────────────
        def read_ultimate_precision_content(filepath):
            file_name = os.path.basename(filepath)
            ext       = file_name.lower().split('.')[-1] if '.' in file_name else ''
            clean_name = re.sub(r'[^a-zA-Z\s]', ' ',
                                file_name.replace('_', ' ').replace('-', ' '))
            content  = (clean_name + " ") * 20
            raw_text = ""
            try:
                if ext == 'pdf':
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for i in range(min(6, len(reader.pages))):
                            page_text = reader.pages[i].extract_text()
                            if page_text:
                                if i == 0:
                                    content += (page_text[:2000] + " ") * 10
                                raw_text += page_text + " "
                elif ext == 'docx':
                    doc = docx.Document(filepath)
                    for para in doc.paragraphs[:40]:
                        raw_text += para.text + " "
                elif ext in ['txt', 'md', 'csv', 'py', 'json']:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_text = f.read(15000)
            except Exception as e:
                print(f"Extraction error: {e}")
    
            raw_text  = raw_text.lower()
            words     = re.findall(r'\b[a-z]{3,15}\b', raw_text)
            stemmed   = [re.sub(r'(ing|tion|ment|ies|s)$', '', w) for w in words]
            raw_text  = " ".join(stemmed)
            noise_re  = (r'\b(chapter|page|university|note|lecture|assignment|pdf'
                        r'|introduction|case|study|faculty|tarc|student|course'
                        r'|module|www|http|com|appendix|reference|conclusion'
                        r'|objective|assessment|rubric|tutorial|practical'
                        r'|guideline|data|result|table)\b')
            raw_text  = re.sub(noise_re, '', raw_text)
            return content + re.sub(r'\s+', ' ', raw_text).strip()
    
        try:
            # ── BRANCH A: 2+ folders, no files → similarity merge (unchanged) ────
            if len(folders_selected) >= 2 and not files_selected:
                progress = QProgressDialog("Merging folders…", "Cancel",
                                        0, len(folders_selected), self)
                progress.setMinimumDuration(0)
                progress.show()
                QApplication.processEvents()
    
                folder_profiles, valid_folders = [], []
                vec_m = TfidfVectorizer(stop_words='english', max_features=2500,
                                        ngram_range=(1, 2), sublinear_tf=True)
    
                for i, folder in enumerate(folders_selected):
                    folder_name = os.path.basename(folder)
                    combined    = (folder_name + " ") * 10
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            combined += read_ultimate_precision_content(
                                os.path.join(root, file))
                            if len(combined) > 80000:
                                break
                    folder_profiles.append(combined)
                    valid_folders.append(folder)
                    progress.setValue(i + 1)
                    QApplication.processEvents()
    
                if len(folder_profiles) >= 2:
                    tfidf_m = vec_m.fit_transform(folder_profiles)
                    sim_mat = cosine_similarity(tfidf_m)
                    best_i, best_j, max_sim = 0, 1, -1
                    for i in range(len(valid_folders)):
                        for j in range(i + 1, len(valid_folders)):
                            if sim_mat[i][j] > max_sim:
                                max_sim = sim_mat[i][j]; best_i = i; best_j = j
    
                    if max_sim > -1:
                        fa, fb = valid_folders[best_i], valid_folders[best_j]
                        parent = fa if len(os.listdir(fa)) >= len(os.listdir(fb)) else fb
                        child  = fb if parent == fa else fa
                        try:
                            target = os.path.join(parent, os.path.basename(child))
                            if os.path.exists(target):
                                target += "_merged"
                            shutil.move(child, target)
                            move_history.append((target, child))
                            results_message += (
                                f"📁 Merged [{os.path.basename(child)}] → "
                                f"[{os.path.basename(parent)}]  "
                                f"({max_sim:.1%} similarity)\n"
                            )
                        except Exception as e:
                            print(f"Merge error: {e}")
    
                progress.close()
                self.handle_satisfaction_check(
                    results_message, "", move_history, current_view_path)
                return
    
            # ── BRANCH B: folders + files → supervised text sort + CNN media ─────
            if folders_selected and files_selected:
    
                # B-1: Images + Videos → CNN
                if image_files or video_files:
                    results_message, cnn_m = self._classify_and_move_images(
                        image_files, video_files,
                        dest_base=current_view_path,
                        move_history=move_history,
                    )
                    metrics_message += cnn_m
    
                # B-2: Text files → TF-IDF + RF + SVM (your original logic)
                if text_files:
                    training_texts, training_labels = [], []
                    folder_paths_map = {}
    
                    for folder in folders_selected:
                        folder_name = os.path.basename(folder)
                        folder_paths_map[folder_name] = folder
                        synthetic = (folder_name + " ") * 50
                        for _ in range(5):
                            training_texts.append(synthetic)
                            training_labels.append(folder_name)
                        for root, dirs, files in os.walk(folder):
                            for file in files:
                                text = read_ultimate_precision_content(
                                    os.path.join(root, file))
                                if text.strip():
                                    training_texts.append(text)
                                    training_labels.append(folder_name)
    
                    unsorted_texts, valid_unsorted = [], []
                    for f in text_files:
                        text = read_ultimate_precision_content(f)
                        if text.strip():
                            unsorted_texts.append(text)
                            valid_unsorted.append(f)
    
                    if valid_unsorted:
                        progress = QProgressDialog(
                            "Analysing text destinations…", "Cancel",
                            0, len(valid_unsorted), self)
                        progress.setMinimumDuration(0)
                        progress.setWindowModality(Qt.WindowModality.WindowModal)
    
                        unique_labels = list(set(training_labels))
                        if len(unique_labels) < 2:
                            # Single-destination direct move
                            tgt_name = unique_labels[0]
                            tgt_path = folder_paths_map[tgt_name]
                            for i, fp in enumerate(valid_unsorted):
                                if progress.wasCanceled():
                                    break
                                fn  = os.path.basename(fp)
                                dst = os.path.join(tgt_path, fn)
                                b, e = os.path.splitext(fn); c = 1
                                while os.path.exists(dst):
                                    dst = os.path.join(tgt_path, f"{b}_copy{c}{e}"); c += 1
                                shutil.move(fp, dst)
                                move_history.append((dst, fp))
                                results_message += (
                                    f"✓ Sorted '{fn}' → [{tgt_name}] "
                                    f"(Single Target)\n")
                                progress.setValue(i + 1); QApplication.processEvents()
                            progress.close()
                            self.handle_satisfaction_check(
                                results_message,
                                metrics_message + "📊 DIRECT SORT: Single destination.\n\n",
                                move_history, current_view_path)
                            return
    
                        vectorizer = TfidfVectorizer(
                            stop_words='english', max_features=5000,
                            ngram_range=(1, 3), min_df=1, max_df=0.80,
                            sublinear_tf=True)
                        X_all  = vectorizer.fit_transform(training_texts)
                        rf     = RandomForestClassifier(n_estimators=300,
                            criterion='entropy', class_weight='balanced',
                            random_state=42)
                        svm    = SVC(kernel='linear', C=3.0,
                            class_weight='balanced', probability=True,
                            random_state=42)
                        rf.fit(X_all, training_labels)
                        svm.fit(X_all, training_labels)
    
                        rf_p  = rf.predict(X_all)
                        svm_p = svm.predict(X_all)
                        metrics_message += (
                            f"📊 ENSEMBLE (TEXT):\n"
                            f"   • RF  precision: "
                            f"{precision_score(training_labels, rf_p, average='weighted', zero_division=0):.2%}\n"
                            f"   • SVM precision: "
                            f"{precision_score(training_labels, svm_p, average='weighted', zero_division=0):.2%}\n\n"
                        )
    
                        X_u     = vectorizer.transform(unsorted_texts)
                        rf_pr   = rf.predict_proba(X_u)
                        svm_pr  = svm.predict_proba(X_u)
                        rf_cls  = rf.classes_
                        svm_cls = svm.classes_
    
                        for i, fp in enumerate(valid_unsorted):
                            if progress.wasCanceled():
                                break
                            rf_pred  = rf_cls[np.argmax(rf_pr[i])]
                            svm_pred = svm_cls[np.argmax(svm_pr[i])]
                            rf_conf  = np.max(rf_pr[i])
                            svm_conf = np.max(svm_pr[i])
    
                            if rf_pred == svm_pred:
                                tgt = rf_pred; icon = "✓"
                            else:
                                tgt  = rf_pred if rf_conf >= svm_conf else svm_pred
                                icon = "⚡ (Tie-Breaker)"
    
                            tgt_path = folder_paths_map.get(tgt)
                            if not tgt_path or not os.path.exists(tgt_path):
                                if rf_pred == svm_pred:
                                    tgt_path = os.path.join(current_view_path, tgt)
                                else:
                                    results_message += (
                                        f"⚠️ Skipped '{os.path.basename(fp)}' "
                                        f"→ [{tgt}] (Hallucinated target)\n")
                                    continue
    
                            fn  = os.path.basename(fp)
                            dst = os.path.join(tgt_path, fn)
                            b, e = os.path.splitext(fn); c = 1
                            while os.path.exists(dst):
                                dst = os.path.join(tgt_path, f"{b}_copy{c}{e}"); c += 1
                            shutil.move(fp, dst)
                            move_history.append((dst, fp))
                            results_message += f"{icon} Sorted '{fn}' → [{tgt}]\n"
                            progress.setValue(i + 1); QApplication.processEvents()
                        progress.close()
    
                self.handle_satisfaction_check(
                    results_message, metrics_message, move_history, current_view_path)
                return
    
            # ── BRANCH C: files only (or folders only) → unsupervised ────────────
            pool = list(files_selected)
            for folder in folders_selected:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        pool.append(os.path.join(root, file))
    
            pool_images = [f for f in pool if Path(f).suffix.lower() in IMAGE_EXTENSIONS]
            pool_videos = [f for f in pool if Path(f).suffix.lower() in VIDEO_EXTENSIONS]
            pool_text   = [f for f in pool
                        if f not in pool_images and f not in pool_videos]
    
            # C-1: Images / Videos → CNN
            if pool_images or pool_videos:
                results_message, cnn_m = self._classify_and_move_images(
                    pool_images, pool_videos,
                    dest_base=current_view_path,
                    move_history=move_history,
                    prefix_msg=results_message,
                )
                metrics_message += cnn_m
    
            # C-2: Text files → KMeans + RF + SVM (your original unsupervised logic)
            if pool_text:
                file_contents, valid_text = [], []
                for f in pool_text:
                    text = read_ultimate_precision_content(f)
                    if text.strip():
                        file_contents.append(text); valid_text.append(f)
    
                if len(valid_text) >= 2:
                    progress = QProgressDialog(
                        "Extracting text clusters…", "Cancel",
                        0, len(valid_text), self)
                    progress.setMinimumDuration(0)
                    progress.setWindowModality(Qt.WindowModality.WindowModal)
    
                    vec_u = TfidfVectorizer(stop_words='english', max_features=3000,
                        ngram_range=(1, 2), min_df=1, max_df=0.90, sublinear_tf=True)
                    X         = vec_u.fit_transform(file_contents)
                    feat_names = vec_u.get_feature_names_out()
    
                    n_clust   = max(1, len(valid_text) // 3)
                    if n_clust >= len(valid_text):
                        n_clust = len(valid_text) - 1
                    kmeans    = KMeans(n_clusters=n_clust, random_state=42,
                                    n_init=30, max_iter=1000)
                    kmeans.fit(X)
                    clabels   = kmeans.labels_
    
                    rf_u  = RandomForestClassifier(n_estimators=300,
                        criterion='entropy', class_weight='balanced', random_state=42)
                    svm_u = SVC(kernel='linear', C=2.0, class_weight='balanced',
                        probability=True, random_state=42)
                    rf_u.fit(X, clabels); svm_u.fit(X, clabels)
                    metrics_message += (
                        "📊 CLUSTER REPORT (TEXT):\n"
                        "   • Logic: KMeans + RF/SVM soft-vote\n\n")
    
                    rf_pr  = rf_u.predict_proba(X)
                    svm_pr = svm_u.predict_proba(X)
                    cls_u  = svm_u.classes_
    
                    for i, fp in enumerate(valid_text):
                        if progress.wasCanceled():
                            break
                        avg       = (rf_pr[i] + svm_pr[i]) / 2.0
                        lbl       = cls_u[np.argmax(avg)]
                        word_idx  = kmeans.cluster_centers_[lbl].argsort()[-1]
                        tgt_name  = feat_names[word_idx].title()
                        if len(tgt_name) < 3:
                            tgt_name = f"Subject_Area_{lbl+1}"
                        tgt_path  = os.path.join(current_view_path, tgt_name)
                        if not os.path.exists(tgt_path):
                            os.mkdir(tgt_path)
                        fn  = os.path.basename(fp)
                        dst = os.path.join(tgt_path, fn)
                        b, e = os.path.splitext(fn); c = 1
                        while os.path.exists(dst):
                            dst = os.path.join(tgt_path, f"{b}_copy{c}{e}"); c += 1
                        shutil.move(fp, dst)
                        move_history.append((dst, fp))
                        results_message += f"✓ Grouped '{fn}' → [{tgt_name}]\n"
                        progress.setValue(i + 1); QApplication.processEvents()
                    progress.close()
    
            if move_history:
                self.handle_satisfaction_check(
                    results_message, metrics_message, move_history, current_view_path)
            else:
                # Show error details if the CNN reported problems, otherwise generic message
                error_lines = [
                    line for line in results_message.splitlines()
                    if line.strip().startswith(("❌", "⚠️"))
                ]
                if error_lines:
                    detail = "\n".join(error_lines)
                    QMessageBox.warning(
                        self, "Smart Organise — Issues Found",
                        f"The AI ran but could not sort the files.\n\n"
                        f"Details:\n{detail}\n\n"
                        f"Check the terminal / console for the full traceback."
                    )
                else:
                    QMessageBox.warning(
                        self, "Nothing Organised",
                        "No recognisable files were found in the selection.\n\n"
                        "Tip: Select image files (.jpg, .png, .webp) or text files "
                        "(.pdf, .docx, .txt) to use Smart Organise."
                    )
    
        except Exception as e:
            QMessageBox.critical(self, "Smart Organise Error",
                                f"Unexpected error:\n\n{e}")
            print(f"[handle_smart_organise] {e}")
 

    def handle_satisfaction_check(self, results, metrics, history, current_path):
        if hasattr(self.files_view, 'file_table'): self.files_view.file_table.load_files(current_path)
        if history:
            dialog = QDialog(self)
            dialog.setWindowTitle("AI Precision Report & Satisfaction Check")
            dialog.resize(750, 550)
            layout = QVBoxLayout(dialog)
            
            instruction_lbl = QLabel("<b>Review the AI sorting results below. Are you satisfied with this organization?</b><br>Selecting 'Undo' will return all items to their original place.")
            layout.addWidget(instruction_lbl)
            
            text_edit = QTextEdit(dialog)
            text_edit.setReadOnly(True)
            text_edit.setText(metrics + results)
            layout.addWidget(text_edit)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            undo_btn = QPushButton("No, Undo Changes")
            keep_btn = QPushButton("Yes, Keep Changes")
            
            undo_btn.clicked.connect(dialog.reject)
            keep_btn.clicked.connect(dialog.accept)
            
            btn_layout.addWidget(undo_btn)
            btn_layout.addWidget(keep_btn)
            layout.addLayout(btn_layout)
            
            if dialog.exec() == QDialog.DialogCode.Rejected:
                undo_progress = QProgressDialog("Restoring originals...", None, 0, len(history), self)
                undo_progress.setMinimumDuration(0); undo_progress.setWindowModality(Qt.WindowModality.WindowModal)
                for i, (new_pos, old_pos) in enumerate(reversed(history)):
                    if os.path.exists(new_pos):
                        shutil.move(new_pos, old_pos)
                        try:
                            if not os.listdir(os.path.dirname(new_pos)): os.rmdir(os.path.dirname(new_pos))
                        except: pass
                    undo_progress.setValue(i + 1); QApplication.processEvents()
                undo_progress.close()
                QMessageBox.information(self, "Restored", "All files and folders have been returned to their original positions.")
                if hasattr(self.files_view, 'file_table'): self.files_view.file_table.load_files(current_path)

    def switch_view(self, identifier):
        if identifier == "settings": self.show_settings_overlay()
        elif identifier in ["sharing", "file_sharing"]:
            self.sharing_view.load_shared_files(); self.stack.setCurrentWidget(self.sharing_view)
            self.top_bar.update_breadcrumbs("File Sharing"); self.sidebar.set_active(identifier) 
        else:
            self.sidebar.set_active(identifier)
            if identifier == "home": self.stack.setCurrentWidget(self.home_view); self.top_bar.update_breadcrumbs("Home")
            elif identifier == "files": self.stack.setCurrentWidget(self.files_view); self.top_bar.update_breadcrumbs(self.files_view.current_path)
            elif identifier == "archive": self.stack.setCurrentWidget(self.archive_view); self.top_bar.update_breadcrumbs("Smart Archive")
            elif identifier == "statistics": self.stack.setCurrentWidget(self.statistics_view); self.top_bar.update_breadcrumbs("Statistics")

    def on_topbar_nav(self, path):
        if self.stack.currentWidget() == self.files_view: self.files_view.on_breadcrumb_clicked(path)
    
    def show_settings_overlay(self):
        if not self.settings_overlay:
            self.settings_overlay = SettingsView(self.user_data); self.settings_overlay.setParent(self) 
            self.settings_overlay.closed.connect(self.hide_settings_overlay); self.settings_overlay.logout_requested.connect(self.handle_logout)
        self.settings_overlay.resize(self.size()); self.settings_overlay.show(); self.settings_overlay.raise_()

    def hide_settings_overlay(self):
        if self.settings_overlay: self.settings_overlay.hide()

    def resizeEvent(self, event):
        if self.settings_overlay and self.settings_overlay.isVisible(): self.settings_overlay.resize(self.size())
        super().resizeEvent(event)
    
    def on_home_folder_opened(self, path):
        self.files_view.navigate_to(path); self.switch_view("files"); self.sidebar.set_active("files")
    
    def handle_search(self, query):
        if self.stack.currentWidget() != self.files_view: self.switch_view("files")
        self.files_view.file_table.filter_files(query)
    
    def mousePressEvent(self, event):
        if self.stack.currentWidget() == self.files_view:
            if event.button() == Qt.MouseButton.BackButton: self.files_view.go_back(); event.accept(); return
            elif event.button() == Qt.MouseButton.ForwardButton: self.files_view.go_forward(); event.accept(); return
        super().mousePressEvent(event)
    
    #CNN logic is here
    def _get_classifier(self):
        """
        Lazy-loads ImageClassifier on first call.  Subsequent calls reuse
        the already-loaded model so the 2-3 second load only happens once.
    
        Raises FileNotFoundError if best_model.pth is missing.
        """
        if self._image_classifier is None:
            if not os.path.exists(CNN_MODEL_PATH):
                raise FileNotFoundError(
                    f"CNN model checkpoint not found:\n{CNN_MODEL_PATH}\n\n"
                    "Make sure best_model.pth is in the models/trained/ folder."
                )
            from src.inference.classifier import ImageClassifier
            print(f"[KemasLah] Loading CNN from {CNN_MODEL_PATH} …")
            self._image_classifier = ImageClassifier(CNN_MODEL_PATH)
            print("[KemasLah] CNN loaded.")
        return self._image_classifier
 
    def _classify_and_move_images(
        self,
        image_paths: list,
        video_paths: list,
        dest_base: str,
        move_history: list,
        prefix_msg: str = "",
    ) -> tuple:
        """
        CNN branch of Smart Organise.
    
        Classifies every image and video file (videos via middle-frame
        extraction) and moves each to:
            dest_base/<PredictedCategory>/filename
    
        Parameters
        ----------
        image_paths  : list of absolute paths to image files
        video_paths  : list of absolute paths to video files
        dest_base    : root folder where category sub-folders are created
        move_history : list — (dest, src) tuples appended for undo support
        prefix_msg   : text already built before calling this (prepended)
    
        Returns
        -------
        (results_msg: str, metrics_msg: str)
        """
        from src.inference.classifier import extract_keyframe
    
        results_msg = prefix_msg
        temp_kfs    = []
    
        # Build the list that goes to the CNN
        classify_paths = list(image_paths)
        kf_to_video: dict[str, str] = {}
    
        for vp in video_paths:
            kf = extract_keyframe(vp, output_dir="outputs/keyframes")
            if kf:
                classify_paths.append(kf)
                kf_to_video[kf] = vp
                temp_kfs.append(kf)
            else:
                results_msg += (
                    f"⚠️ Could not read keyframe from "
                    f"'{os.path.basename(vp)}' — skipped.\n"
                )
    
        if not classify_paths:
            return results_msg, ""
    
        # Load the model
        try:
            classifier = self._get_classifier()
        except FileNotFoundError as e:
            results_msg += f"❌ CNN unavailable: {e}\n"
            return results_msg, "❌ CNN model missing — images not sorted.\n\n"
    
        # Progress dialog
        total    = len(classify_paths)
        progress = QProgressDialog(
            f"🖼️  CNN classifying {total} image/video file(s)…",
            "Cancel", 0, total, self,
        )
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
    
        try:
            cnn_results = classifier.classify_batch(classify_paths, batch_size=16)
        except Exception as e:
            progress.close()
            results_msg += f"❌ CNN batch error: {e}\n"
            return results_msg, "❌ CNN batch inference failed.\n\n"
    
        confident = fallback = 0
    
        for idx, result in enumerate(cnn_results):
            if progress.wasCanceled():
                break
    
            clf_path   = result["file_path"]
            category   = result["category"]   # one of the 10 KemasLah categories
            confidence = result["confidence"]
            accepted   = result["accepted"]
    
            # Map keyframe back to the original video path if needed
            real_path = kf_to_video.get(clf_path, clf_path)
            file_name = os.path.basename(real_path)
    
            # Create category folder (e.g.  …/Vacation_Travel/)
            dest_folder = os.path.join(dest_base, category)
            os.makedirs(dest_folder, exist_ok=True)
    
            # Avoid overwriting an existing file of the same name
            dest_file   = os.path.join(dest_folder, file_name)
            base, ext   = os.path.splitext(file_name)
            counter     = 1
            while os.path.exists(dest_file):
                dest_file = os.path.join(dest_folder, f"{base}_copy{counter}{ext}")
                counter  += 1
    
            try:
                shutil.move(real_path, dest_file)
                move_history.append((dest_file, real_path))
                status = "✓" if accepted else "⚡"
                results_msg += (
                    f"{status} CNN: '{file_name}' → [{category}] "
                    f"({confidence:.0%})\n"
                )
                if accepted:
                    confident += 1
                else:
                    fallback  += 1
            except Exception as e:
                results_msg += f"⚠️ Could not move '{file_name}': {e}\n"
    
            progress.setValue(idx + 1)
            QApplication.processEvents()
    
        progress.close()
    
        # Clean up temporary keyframe JPEGs
        for kf in temp_kfs:
            try:
                os.remove(kf)
            except Exception:
                pass
    
        metrics_msg = (
            f"📊 CNN IMAGE CLASSIFICATION REPORT:\n"
            f"   • Backbone          : ResNet50 (Places365 + MS COCO)\n"
            f"   • Output categories : 10 KemasLah categories\n"
            f"   • Files processed   : {total}\n"
            f"   • High confidence   : {confident}  "
            f"({confident/total:.0%} of media)\n"
            f"   • Fallback category : {fallback}\n\n"
        )
        return results_msg, metrics_msg
    
    
    def _on_cnn_image_match(self, name: str, full_path: str,
                            category: str, confidence: float):
        """
        Slot for CNNSearchWorker.match_found.
        Adds the matched image into the file table alongside text results.
        """
        # _add_search_row is the same helper used by the text SearchWorker
        self.files_view.file_table._add_search_row(name, full_path, is_dir=False)
    
    
    def _on_cnn_search_done(self, scanned: int, matched: int):
        """Slot for CNNSearchWorker.search_finished."""
        print(f"[CNN Search] Done — scanned {scanned} media files, "
            f"matched {matched}.")
    
    
    def _on_cnn_search_error(self, message: str):
        """Slot for CNNSearchWorker.error_occurred."""
        # Silent — text search still works even if CNN is unavailable.
        print(f"[CNN Search] Error (non-fatal): {message}")  

class KemaslahApp(QMainWindow):
    def __init__(self):
        super().__init__(); create_db(); self.setWindowTitle("Kemaslah - Smart File Manager")
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack); self.auth_window = AuthWindow()
        self.stack.addWidget(self.auth_window); self.file_manager = None
        login_page = self.auth_window.stack.widget(0)
        if hasattr(login_page, 'login_successful'): login_page.login_successful.connect(self.on_login_success)
        if hasattr(login_page, 'skip_login_clicked'): login_page.skip_login_clicked.connect(self.on_skip_login)
        self.setFixedSize(1000, 750)
        
    def on_login_success(self, user_data):
        self._destroy_file_manager(); self.file_manager = SmartFileManager(user_data, auth_window=self.auth_window)
        self.file_manager.logout_requested.connect(self.on_logout); self.stack.addWidget(self.file_manager)
        self.stack.setCurrentWidget(self.file_manager); self.file_manager.switch_view("home")
        self.setMinimumSize(1200, 800); self.showMaximized()
    
    def on_skip_login(self):
        guest_data = {"username": "Guest User", "email": "guest@local", "initials": "GU", "display_name": "Guest User"}
        if self.file_manager is None:
            self.file_manager = SmartFileManager(guest_data, auth_window=None); self.file_manager.logout_requested.connect(self.on_guest_exit)
            self.stack.addWidget(self.file_manager)
        self.stack.setCurrentWidget(self.file_manager); self.file_manager.switch_view("home")
        self.setMinimumSize(1200, 800); self.showMaximized()
    
    def on_guest_exit(self):
        reply = QMessageBox.question(self, 'Logout', 'Exit guest mode and return to login?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self._destroy_file_manager(); self.stack.setCurrentWidget(self.auth_window); self.auth_window.stack.setCurrentIndex(0); self.setFixedSize(1000, 750); self.showNormal()
            
    def on_logout(self):
        self._destroy_file_manager(); login_page = self.auth_window.stack.widget(0)
        if hasattr(login_page, 'clear_fields'): login_page.clear_fields()
        self.stack.setCurrentWidget(self.auth_window); self.setFixedSize(1000, 750); self.showNormal(); self.auth_window.stack.setCurrentIndex(0)

    def _destroy_file_manager(self):
        if self.file_manager is not None: self.stack.removeWidget(self.file_manager); self.file_manager.deleteLater(); self.file_manager = None

    def update_all_pages(self, lang_code):
        if hasattr(self.auth_window, 'update_all_pages'): self.auth_window.update_all_pages(lang_code)
        if self.file_manager:
            self.file_manager.top_bar.update_translations(lang_code); self.file_manager.sidebar.update_translations(lang_code)
            self.file_manager.action_bar.update_translations(lang_code); self.file_manager.statistics_view.update_translations(lang_code)
            self.file_manager.home_view.update_translations(lang_code)
            if hasattr(self.file_manager, 'sharing_view'): self.file_manager.sharing_view.update_translations(lang_code)

def run_server():
    log = logging.getLogger('werkzeug'); log.setLevel(logging.ERROR); flask_app.run(port=5000, use_reloader=False, debug=False)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True); server_thread.start()
    app = QApplication(sys.argv); app.setStyle('Fusion'); window = KemaslahApp(); window.show(); sys.exit(app.exec())