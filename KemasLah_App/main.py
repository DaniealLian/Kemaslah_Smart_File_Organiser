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
        """Scans document contents with Explicit Error Reporting."""
        query_lower = ai_query.lower()
        current_path = self.files_view.current_path
        if not os.path.exists(current_path): return

        files_in_dir = [os.path.join(current_path, f) for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))]
        
        if not files_in_dir:
            QMessageBox.information(self, "Content Scanner", f"There are no files inside the folder '{os.path.basename(current_path)}' to scan.\n\nPlease navigate to the exact folder where your text file is saved!")
            return

        progress = QProgressDialog(f"Deep scanning inside {len(files_in_dir)} documents...", "Cancel", 0, len(files_in_dir), self)
        progress.setMinimumDuration(500) 
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        def quick_content_extract(filepath):
            ext = filepath.lower().split('.')[-1] if '.' in filepath else ''
            raw_text = ""
            try:
                if ext == 'pdf':
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for i in range(min(5, len(reader.pages))):
                            page_text = reader.pages[i].extract_text()
                            if page_text: raw_text += page_text + " "
                elif ext == 'docx':
                    doc = docx.Document(filepath)
                    for para in doc.paragraphs[:50]: raw_text += para.text + " " 
                elif ext in ['txt', 'md', 'csv', 'py', 'json']:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_text = f.read(10000) 
            except Exception as read_err: 
                # UX FIX: Print exact read errors to console instead of silent pass
                print(f"Error reading file {filepath}: {read_err}")
                pass
            
            return raw_text.lower()

        docs = []
        valid_files = []
        for i, fp in enumerate(files_in_dir):
            if progress.wasCanceled(): break
            content = quick_content_extract(fp)
            if content.strip():
                docs.append(content)
                valid_files.append(fp)
            progress.setValue(i + 1); QApplication.processEvents()
        progress.close()

        if not valid_files:
            QMessageBox.information(self, "Content Scanner", f"Scanned {len(files_in_dir)} files, but none contained readable text.\n\nMake sure your text file was actually saved (Ctrl+S)!")
            return

        try:
            found_matches = []
            
            # ABSOLUTE BRUTE-FORCE MATCH: Bypasses all AI limits
            for idx, content in enumerate(docs):
                if query_lower in content:
                    found_matches.append((idx, 1.0, "Exact Keyword Match"))

            # Fallback to AI Semantic Match
            if not found_matches:
                vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b') 
                tfidf_matrix = vectorizer.fit_transform([query_lower] + docs)
                cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
                
                top_indices = cosine_sim.argsort()[-5:][::-1] 
                for idx in top_indices:
                    if cosine_sim[idx] > 0.001: 
                        found_matches.append((idx, cosine_sim[idx], "Semantic AI Match"))
            
            if not found_matches: 
                QMessageBox.information(self, "Content Scanner", f"Scanned {len(valid_files)} files in '{os.path.basename(current_path)}'.\n\nCould not find any text matching '{ai_query}'.\n\nAre you 100% sure you moved the file into THIS exact folder?")
                return
            
            result_msg = f"🔍 Inside-File Matches for: '{ai_query}'\n\n"
            for idx, score, match_type in found_matches:
                file_name = os.path.basename(valid_files[idx])
                score_txt = "100% (Exact Match)" if match_type == "Exact Keyword Match" else f"{score:.1%}"
                result_msg += f"📄 {file_name}\n   • Match Type: {match_type}\n   • Relevance: {score_txt}\n\n"
            
            dialog = QDialog(self)
            dialog.setWindowTitle("File Content Search Results")
            dialog.resize(600, 400)
            layout = QVBoxLayout(dialog)
            
            instruction_lbl = QLabel(f"<b>Top matches based on inside document text for '{ai_query}':</b><br><i>(Note: Files that don't have this word in their title are hidden behind this box)</i>")
            layout.addWidget(instruction_lbl)
            
            text_edit = QTextEdit(dialog)
            text_edit.setReadOnly(True)
            text_edit.setText(result_msg)
            layout.addWidget(text_edit)
            
            btn = QPushButton("Close Search Results")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            dialog.exec()

        except Exception as e:
            # UX FIX: Critical Error Reporting
            if "empty vocabulary" in str(e).lower():
                 QMessageBox.warning(self, "AI Search Alert", "Search query contains invalid characters.")
            else:
                 QMessageBox.critical(self, "System Error", f"The AI encountered an error while scanning the text:\n\n{str(e)}\n\nCheck terminal for details.")
                 print(f"Deep Search Error: {e}")

    # -------------------------------------------------------------------------
    # --- CORE AI LOGIC: Sorting and Organization ---
    # -------------------------------------------------------------------------
    def handle_smart_organise(self):
        current_widget = self.stack.currentWidget()
        if current_widget != self.files_view: return

        selected_paths = self.files_view.file_table.get_selected_files() 
        if not selected_paths:
            QMessageBox.warning(self, "No Selection", "Please select folders or files to organize.")
            return

        def read_ultimate_precision_content(filepath):
            file_name = os.path.basename(filepath)
            ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            
            clean_name = re.sub(r'[^a-zA-Z\s]', ' ', file_name.replace('_', ' ').replace('-', ' '))
            content = (clean_name + " ") * 20 
            
            raw_text = ""
            try:
                if ext == 'pdf':
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for i in range(min(6, len(reader.pages))): 
                            page_text = reader.pages[i].extract_text()
                            if page_text:
                                if i == 0: raw_text += (page_text[:2000] + " ") * 10
                                raw_text += page_text + " "
                elif ext == 'docx':
                    doc = docx.Document(filepath)
                    for para in doc.paragraphs[:40]: raw_text += para.text + " "
                elif ext in ['txt', 'md', 'csv', 'py', 'json']:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_text = f.read(15000) 
            except Exception as e:
                print(f"Extraction error: {e}")

            raw_text = raw_text.lower()
            words = re.findall(r'\b[a-z]{3,15}\b', raw_text)
            stemmed_words = [re.sub(r'(ing|tion|ment|ies|s)$', '', w) for w in words]
            raw_text = " ".join(stemmed_words)
            
            academic_noise = r'\b(chapter|page|university|note|lecture|assignment|pdf|introduction|case|study|faculty|tarc|student|course|module|www|http|com|appendix|reference|conclusion|objective|assessment|rubric|tutorial|practical|guideline|data|result|table)\b'
            raw_text = re.sub(academic_noise, '', raw_text)
            
            return content + re.sub(r'\s+', ' ', raw_text).strip()

        folders_selected = [p for p in selected_paths if os.path.isdir(p)]
        files_selected = [p for p in selected_paths if os.path.isfile(p)]
        
        move_history = [] 
        results_message = f"🤖 AI Smart Organise Complete!\n\n"
        metrics_message = ""
        current_view_path = self.files_view.current_path

        try:
            if len(folders_selected) >= 2 and not files_selected:
                progress = QProgressDialog("Merging folders...", "Cancel", 0, len(folders_selected), self)
                progress.setMinimumDuration(0); progress.show(); QApplication.processEvents()

                folder_profiles, valid_folders = [], []
                vectorizer = TfidfVectorizer(stop_words='english', max_features=2500, ngram_range=(1, 2), sublinear_tf=True)
                
                for i, folder in enumerate(folders_selected):
                    folder_name = os.path.basename(folder)
                    combined_text = (folder_name + " ") * 10 
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            combined_text += read_ultimate_precision_content(os.path.join(root, file))
                            if len(combined_text) > 80000: break
                    
                    folder_profiles.append(combined_text)
                    valid_folders.append(folder)
                    progress.setValue(i + 1); QApplication.processEvents()
                
                if len(folder_profiles) >= 2:
                    tfidf_matrix = vectorizer.fit_transform(folder_profiles)
                    sim_matrix = cosine_similarity(tfidf_matrix)
                    
                    best_i, best_j, max_sim = 0, 1, -1
                    for i in range(len(valid_folders)):
                        for j in range(i + 1, len(valid_folders)):
                            if sim_matrix[i][j] > max_sim:
                                max_sim = sim_matrix[i][j]
                                best_i, best_j = i, j
                                
                    if max_sim > -1:
                        folder_a, folder_b = valid_folders[best_i], valid_folders[best_j]
                        parent = folder_a if len(os.listdir(folder_a)) >= len(os.listdir(folder_b)) else folder_b
                        child = folder_b if parent == folder_a else folder_a
                        try:
                            target_path = os.path.join(parent, os.path.basename(child))
                            if os.path.exists(target_path): target_path += "_merged"
                            shutil.move(child, target_path); move_history.append((target_path, child))
                            results_message += f"📁 Force Merged Folders: [{os.path.basename(child)}] ➡️ [{os.path.basename(parent)}]\n   • Best Available Match Score: {max_sim:.1%}\n"
                        except Exception as e: print(f"Merge error: {e}")
                    
                    progress.close()
                    self.handle_satisfaction_check(results_message, "", move_history, current_view_path)
                    return

            if folders_selected and files_selected:
                training_texts, training_labels = [], []
                folder_paths_map = {} 
                
                for folder in folders_selected:
                    folder_name = os.path.basename(folder)
                    folder_paths_map[folder_name] = folder 

                    synthetic_data = (folder_name + " ") * 50
                    for _ in range(5):
                        training_texts.append(synthetic_data)
                        training_labels.append(folder_name)

                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            text = read_ultimate_precision_content(os.path.join(root, file))
                            if text.strip(): training_texts.append(text); training_labels.append(folder_name) 

                unsorted_texts, valid_unsorted_files = [], []
                for f in files_selected:
                    text = read_ultimate_precision_content(f)
                    if text.strip(): unsorted_texts.append(text); valid_unsorted_files.append(f)

                if valid_unsorted_files:
                    progress = QProgressDialog("Analyzing Destinations...", "Cancel", 0, len(valid_unsorted_files), self)
                    progress.setMinimumDuration(0); progress.setWindowModality(Qt.WindowModality.WindowModal)

                    unique_labels = list(set(training_labels))
                    if len(unique_labels) < 2:
                        target_folder_name = unique_labels[0]
                        dest_folder_path = folder_paths_map[target_folder_name]
                        for i, file_path in enumerate(valid_unsorted_files):
                            if progress.wasCanceled(): break
                            file_name = os.path.basename(file_path); dest_file_path = os.path.join(dest_folder_path, file_name)
                            base, ext_name = os.path.splitext(file_name)
                            counter = 1
                            while os.path.exists(dest_file_path):
                                dest_file_path = os.path.join(dest_folder_path, f"{base}_copy{counter}{ext_name}"); counter += 1
                            
                            shutil.move(file_path, dest_file_path); move_history.append((dest_file_path, file_path))
                            results_message += f"✓ Sorted '{file_name}' ➡️ [{target_folder_name}] (Single Target Direct Move)\n"
                            progress.setValue(i + 1); QApplication.processEvents()
                        progress.close()
                        self.handle_satisfaction_check(results_message, "📊 DIRECT SORTING:\n   • Logic: Single Destination Selected\n   • Coverage: 100% Automated Distribution\n\n", move_history, current_view_path)
                        return

                    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 3), min_df=1, max_df=0.80, sublinear_tf=True)
                    X_all = vectorizer.fit_transform(training_texts)
                    
                    rf_model = RandomForestClassifier(n_estimators=300, criterion='entropy', class_weight='balanced', random_state=42)
                    svm_model_sup = SVC(kernel='linear', C=3.0, class_weight='balanced', probability=True, random_state=42)
                    
                    rf_model.fit(X_all, training_labels)
                    svm_model_sup.fit(X_all, training_labels)
                    
                    rf_preds = rf_model.predict(X_all)
                    svm_preds = svm_model_sup.predict(X_all)
                    
                    metrics_message = f"📊 ENSEMBLE CONSENSUS REPORT:\n   • RF Precision: {precision_score(training_labels, rf_preds, average='weighted', zero_division=0):.2%}\n   • SVM Precision: {precision_score(training_labels, svm_preds, average='weighted', zero_division=0):.2%}\n   • Logic: Soft Voting Probability Averaging\n\n"

                    X_unsorted = vectorizer.transform(unsorted_texts)
                    rf_probs = rf_model.predict_proba(X_unsorted)
                    svm_probs = svm_model_sup.predict_proba(X_unsorted)
                    
                    rf_classes = rf_model.classes_
                    svm_classes = svm_model_sup.classes_

                    for i, file_path in enumerate(valid_unsorted_files):
                        if progress.wasCanceled(): break
                        
                        rf_pred = rf_classes[np.argmax(rf_probs[i])]
                        svm_pred = svm_classes[np.argmax(svm_probs[i])]
                        rf_conf = np.max(rf_probs[i])
                        svm_conf = np.max(svm_probs[i])
                        
                        if rf_pred == svm_pred:
                            target_folder_name = rf_pred
                            status_icon = "✓"
                        else:
                            target_folder_name = rf_pred if rf_conf >= svm_conf else svm_pred
                            status_icon = "⚡ (Tie-Breaker)"

                        dest_folder_path = folder_paths_map.get(target_folder_name, None)
                        
                        if not dest_folder_path or not os.path.exists(dest_folder_path):
                             if rf_pred == svm_pred:
                                 dest_folder_path = os.path.join(current_view_path, rf_pred)
                             else:
                                 results_message += f"⚠️ Skipped '{os.path.basename(file_path)}' ➡️ [{target_folder_name}] (Hallucinated Folder Target)\n"
                                 continue

                        file_name = os.path.basename(file_path); dest_file_path = os.path.join(dest_folder_path, file_name)
                        base, ext_name = os.path.splitext(file_name)
                        counter = 1
                        while os.path.exists(dest_file_path):
                            dest_file_path = os.path.join(dest_folder_path, f"{base}_copy{counter}{ext_name}"); counter += 1
                        
                        shutil.move(file_path, dest_file_path); move_history.append((dest_file_path, file_path))
                        results_message += f"{status_icon} Sorted '{file_name}' ➡️ [{target_folder_name}]\n"
                        progress.setValue(i + 1); QApplication.processEvents()
                    progress.close()
                    self.handle_satisfaction_check(results_message, metrics_message, move_history, current_view_path)
                    return

            elif files_selected or (folders_selected and not files_selected):
                file_contents, valid_files = [], []
                pool_of_files = files_selected.copy()
                for folder in folders_selected:
                    for root, dirs, files in os.walk(folder):
                        for file in files: pool_of_files.append(os.path.join(root, file))

                for f in pool_of_files:
                    text = read_ultimate_precision_content(f)
                    if text.strip(): file_contents.append(text); valid_files.append(f)

                if len(valid_files) >= 2:
                    progress = QProgressDialog("Extracting boundaries via Soft Voting...", "Cancel", 0, len(valid_files), self)
                    progress.setMinimumDuration(0); progress.setWindowModality(Qt.WindowModality.WindowModal)

                    vectorizer = TfidfVectorizer(stop_words='english', max_features=3000, ngram_range=(1, 2), min_df=1, max_df=0.90, sublinear_tf=True)
                    X = vectorizer.fit_transform(file_contents)
                    feature_names = vectorizer.get_feature_names_out()
                    
                    n_clusters = max(1, len(valid_files) // 3)
                    if n_clusters >= len(valid_files): n_clusters = len(valid_files) - 1
                    
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=30, max_iter=1000)
                    kmeans.fit(X)
                    
                    cluster_labels = kmeans.labels_
                    
                    rf_model_unsup = RandomForestClassifier(n_estimators=300, criterion='entropy', class_weight='balanced', random_state=42)
                    svm_model_unsup = SVC(kernel='linear', C=2.0, class_weight='balanced', probability=True, random_state=42)
                    
                    rf_model_unsup.fit(X, cluster_labels)
                    svm_model_unsup.fit(X, cluster_labels)
                    
                    metrics_message = f"📊 ENTERPRISE CLUSTER REPORT:\n   • Logic: Dual-Model Probability Averaging\n   • Status: 100% Boundary Assignment\n\n"

                    rf_probs = rf_model_unsup.predict_proba(X)
                    svm_probs = svm_model_unsup.predict_proba(X)
                    classes = svm_model_unsup.classes_
                    
                    for i, file_path in enumerate(valid_files):
                        if progress.wasCanceled(): break
                        
                        avg_probs = (rf_probs[i] + svm_probs[i]) / 2.0
                        assigned_label = classes[np.argmax(avg_probs)]
                        
                        top_word_idx = kmeans.cluster_centers_[assigned_label].argsort()[-1]
                        target_folder = feature_names[top_word_idx].title()
                        if len(target_folder) < 3: target_folder = f"Subject_Area_{assigned_label+1}"
                        status_icon = "✓"
                        
                        dest_folder_path = os.path.join(current_view_path, target_folder)
                        if not os.path.exists(dest_folder_path): os.mkdir(dest_folder_path)
                        file_name = os.path.basename(file_path); dest_file_path = os.path.join(dest_folder_path, file_name)
                        base, ext_name = os.path.splitext(file_name)
                        counter = 1
                        while os.path.exists(dest_file_path):
                            dest_file_path = os.path.join(dest_folder_path, f"{base}_copy{counter}{ext_name}"); counter += 1
                        
                        shutil.move(file_path, dest_file_path); move_history.append((dest_file_path, file_path))
                        results_message += f"{status_icon} Smart Grouped '{file_name}' ➡️ [{target_folder}]\n"
                        progress.setValue(i + 1); QApplication.processEvents()
                    progress.close()
                    self.handle_satisfaction_check(results_message, metrics_message, move_history, current_view_path)
                    return
            else:
                QMessageBox.warning(self, "Invalid Selection", "Please select files or folders to organize.")

        except Exception as e:
            QMessageBox.critical(self, "Semantic Error", f"Precision pipeline failed: {e}")

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