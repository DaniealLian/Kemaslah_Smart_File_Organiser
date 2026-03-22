"""
classifier_worker.py
--------------------
Place this file at: src/inference/classifier_worker.py

A QThread wrapper that runs CNN image/video classification in the
background so the PyQt6 UI never freezes during Smart Search.

How it fits into KemasLah:
    When the user types a search query (e.g. "vacation") and hits Enter,
    the text SearchWorker in file_table.py handles filenames and document
    content.  This worker handles image and video files — it classifies
    every .jpg/.png/.mp4 etc. in the current folder using the trained
    ResNet50 model, then emits match_found() for every file whose
    predicted KemasLah category matches the query.

Matching logic — the 10 KemasLah categories are:
    Vacation_Travel, Work_Professional, Food_Dining, Nature_Outdoors,
    Home_Interior, People_Events, Pets_Animals, Vehicles_Transport,
    Sports_Fitness, Screenshots_Documents

Query words are matched against category words with substring logic:
    "vacation" → Vacation_Travel    ✓
    "food"     → Food_Dining        ✓
    "pet"      → Pets_Animals       ✓  (substring of "pets")
    "outdoor"  → Nature_Outdoors    ✓
    "vehicle"  → Vehicles_Transport ✓
"""

import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

# Mirrors classifier.py — keep in sync if you add new extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif",
                    ".heic", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv"}


def _query_matches_category(query: str, category: str) -> bool:
    """
    True if any word in `query` overlaps (as substring) with any word
    in `category` (split on underscore).  Min query word length: 3.
    """
    q_words = [w.lower() for w in query.split() if len(w) >= 3]
    c_words = [w.lower() for w in category.split("_")]
    for qw in q_words:
        for cw in c_words:
            if qw in cw or cw in qw:
                return True
    return False


class CNNSearchWorker(QThread):
    """
    Background thread — classifies all images/videos in a folder and
    emits match_found() for every file that matches the search query.

    Signals
    -------
    match_found(name: str, full_path: str, category: str, confidence: float)
    search_finished(total_scanned: int, total_matched: int)
    error_occurred(message: str)
    """

    match_found     = pyqtSignal(str, str, str, float)
    search_finished = pyqtSignal(int, int)
    error_occurred  = pyqtSignal(str)

    def __init__(self, query: str, search_path: str, model_path: str,
                 batch_size: int = 16, parent=None):
        super().__init__(parent)
        self.query       = query
        self.search_path = search_path
        self.model_path  = model_path
        self.batch_size  = batch_size
        self._running    = True

    def stop(self):
        self._running = False

    # ── helpers ───────────────────────────────────────────────────────────────

    def _collect_media(self) -> list[str]:
        all_exts = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
        result   = []
        try:
            for entry in os.scandir(self.search_path):
                if not self._running:
                    break
                if entry.is_file() and Path(entry.name).suffix.lower() in all_exts:
                    result.append(entry.path)
        except PermissionError:
            pass
        return result

    def _extract_keyframe(self, video_path: str) -> str | None:
        try:
            import cv2
            cap   = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            tmp = os.path.join(os.getcwd(), "outputs", "keyframes")
            os.makedirs(tmp, exist_ok=True)
            out  = os.path.join(tmp, Path(video_path).stem + "_kf.jpg")
            cv2.imwrite(out, frame)
            return out
        except Exception as e:
            print(f"[CNNSearch] Keyframe failed: {e}")
            return None

    # ── thread entry point ────────────────────────────────────────────────────

    def run(self):
        try:
            from src.inference.classifier import ImageClassifier
            classifier = ImageClassifier(self.model_path)
        except FileNotFoundError as e:
            self.error_occurred.emit(str(e))
            return
        except Exception as e:
            self.error_occurred.emit(f"CNN model failed to load:\n{e}")
            return

        all_media = self._collect_media()
        if not all_media or not self._running:
            self.search_finished.emit(0, 0)
            return

        # Build classify list — videos become a keyframe, images go directly
        classify_list: list[str] = []
        actual_map:   dict[str, str] = {}
        temp_kfs:     list[str] = []

        for path in all_media:
            if not self._running:
                break
            if Path(path).suffix.lower() in VIDEO_EXTENSIONS:
                kf = self._extract_keyframe(path)
                if kf:
                    classify_list.append(kf)
                    actual_map[kf] = path
                    temp_kfs.append(kf)
            else:
                classify_list.append(path)
                actual_map[path] = path

        if not classify_list:
            self.search_finished.emit(0, 0)
            return

        scanned = matched = 0
        for i in range(0, len(classify_list), self.batch_size):
            if not self._running:
                break
            batch = classify_list[i : i + self.batch_size]
            try:
                results = classifier.classify_batch(batch)
            except Exception as e:
                print(f"[CNNSearch] Batch error: {e}")
                continue

            for r in results:
                scanned += 1
                real_path = actual_map.get(r["file_path"], r["file_path"])
                if _query_matches_category(self.query, r["category"]):
                    matched += 1
                    self.match_found.emit(
                        os.path.basename(real_path),
                        real_path,
                        r["category"],
                        r["confidence"],
                    )

        for kf in temp_kfs:
            try:
                os.remove(kf)
            except Exception:
                pass

        self.search_finished.emit(scanned, matched)
