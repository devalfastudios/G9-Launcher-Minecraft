import sys
import uuid
import os
import shutil
import json
import platform
import subprocess

# ── Хелпер: запускає процес БЕЗ спалаху CMD-вікна на Windows ──────────
def _run_hidden(*args, **kwargs):
    """subprocess.run з прихованим вікном (для .exe на Windows)."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    kwargs.setdefault("startupinfo", si)
    kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(*args, **kwargs)
import ctypes
import time
import threading
from threading import Thread
 
try:
    myappid = 'alfastudios.g9launcher.v14'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass
 
try:
    import psutil
except ImportError:
    psutil = None
 
try:
    import minecraft_launcher_lib
    HAS_LAUNCHER_LIB = True
except ImportError:
    HAS_LAUNCHER_LIB = False
 
try:
    from pypresence import Presence
    HAS_PYPRESENCE = True
except ImportError:
    HAS_PYPRESENCE = False
 
import urllib.request
 
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, QComboBox,
                             QProgressBar, QStackedWidget, QSlider, QLineEdit,
                             QCheckBox, QListWidget, QInputDialog, QMessageBox,
                             QDialog, QFileDialog, QGroupBox, QFormLayout,
                             QScrollArea, QSizePolicy, QFrame, QColorDialog,
                             QSizeGrip, QTabWidget)
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from PyQt5.QtCore import (Qt, QTimer, QSize, QPoint, QPropertyAnimation,
                           QEasingCurve, QRect, pyqtProperty, QThread, pyqtSignal,
                           QObject, QParallelAnimationGroup, QSequentialAnimationGroup)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QPixmap, QImage
 
HAS_WEBENGINE = False
 
# ─────────────────────────── THEMES ───────────────────────────
DARK_THEME = """
QScrollBar:vertical {
    border: none; background: #2b2b2b; width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #4caf50; min-height: 20px; border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }
QPushButton { background-color: #388e3c; color: white; border: 2px solid #2e7d32; padding: 6px; border-radius: 4px; font-weight: bold; }
QPushButton:hover { background-color: #4caf50; border: 2px solid #388e3c; }
QPushButton:pressed { background-color: #2e7d32; }
QComboBox, QLineEdit, QListWidget { background-color: #3c3f41; border: 1px solid #555; color: white; padding: 4px; }
QProgressBar { border: 1px solid #555; background-color: #3c3f41; height: 10px; text-align: center; color: transparent; }
QProgressBar::chunk { background-color: #4caf50; }
#PlayButton { font-size: 16px; padding: 10px; background-color: #4caf50; border: 2px solid #388e3c; }
#PlayButton:hover { background-color: #66bb6a; }
#StopButton { background-color: #e53935; border: 2px solid #c62828; }
#StopButton:hover { background-color: #ef5350; }
"""
 
LOGO_HTML = "<span style='color:#4da6ff;'>G</span><span style='color:#ffeb3b;'>9</span> <span style='color:#4caf50;'>Launcher</span>"

CONFIG_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), '.g9launcher')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'launcher_config.json')
NICKS_FILE = os.path.join(CONFIG_DIR, 'nicknames.json')

# ─────────────────────────── AUTO-UPDATE INFRASTRUCTURE ───────────────────────────
_LAUNCHER_VERSION = "1.4.1"
_UPDATE_REPO = "devalfastudios/G9-Launcher"  # змінити на реальний репо при випуску 1.5
_UPDATE_API  = f"https://api.github.com/repos/{_UPDATE_REPO}/releases/latest"
_UPDATE_CACHE_FILE = os.path.join(
    os.getenv('APPDATA', os.path.expanduser('~')), '.g9launcher', '_update_cache.json'
)

def _fetch_latest_release_info():
    """Завантажує інформацію про останній реліз з GitHub API. Повертає dict або None."""
    try:
        req = urllib.request.Request(
            _UPDATE_API,
            headers={"User-Agent": f"G9Launcher/{_LAUNCHER_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception:
        return None

def _is_newer_version(remote: str, local: str) -> bool:
    """Повертає True якщо remote > local (порівняння x.y.z)."""
    try:
        r = tuple(int(x) for x in remote.lstrip("v").split("."))
        l = tuple(int(x) for x in local.lstrip("v").split("."))
        return r > l
    except Exception:
        return False

def _check_for_update_async(callback=None):
    """Асинхронно перевіряє наявність оновлення. callback(tag, url) або callback(None, None)."""
    def _worker():
        info = _fetch_latest_release_info()
        if info:
            tag = info.get("tag_name", "")
            url = info.get("html_url", "")
            try:
                cache = {"tag": tag, "url": url}
                os.makedirs(os.path.dirname(_UPDATE_CACHE_FILE), exist_ok=True)
                with open(_UPDATE_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except Exception:
                pass
            if callback and _is_newer_version(tag, _LAUNCHER_VERSION):
                try:
                    callback(tag, url)
                except Exception:
                    pass
        else:
            if callback:
                try:
                    callback(None, None)
                except Exception:
                    pass
    Thread(target=_worker, daemon=True).start()

def _get_cached_update_info():
    """Повертає (tag, url) з кешу або (None, None)."""
    try:
        with open(_UPDATE_CACHE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        tag = d.get("tag", "")
        url = d.get("url", "")
        if tag and _is_newer_version(tag, _LAUNCHER_VERSION):
            return tag, url
    except Exception:
        pass
    return None, None
 
 
# ─────────────────────────── RESIZE GRIP ───────────────────────────
class ResizeGrip(QWidget):
    """Invisible resize grip in bottom-right corner."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setCursor(Qt.SizeFDiagCursor)
        self._resizing = False
        self._start_pos = None
        self._start_geom = None
 
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#4caf50"))
        for i in range(3):
            offset = 4 + i * 4
            p.drawLine(offset, 14, 14, offset)
        p.end()
 
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._start_pos = event.globalPos()
            self._start_geom = self.window().geometry()
 
    def mouseMoveEvent(self, event):
        if self._resizing and self._start_pos:
            delta = event.globalPos() - self._start_pos
            geo = self._start_geom
            new_w = max(750, geo.width() + delta.x())
            new_h = max(500, geo.height() + delta.y())
            win = self.window()
            win.setGeometry(geo.x(), geo.y(), new_w, new_h)
            # Scale fonts dynamically
            win._update_scale()
 
    def mouseReleaseEvent(self, event):
        self._resizing = False
 
 
# ─────────────────────────── NO-SCROLL WIDGETS ───────────────────────────
class NoScrollSlider(QSlider):
    """QSlider that ignores wheel events so ScrollArea can scroll instead."""
    def wheelEvent(self, event):
        event.ignore()
 
class NoScrollCombo(QComboBox):
    """QComboBox that ignores wheel events so ScrollArea can scroll instead."""
    def wheelEvent(self, event):
        event.ignore()
 
 
# ─────────────────────────── TOGGLE SWITCH ───────────────────────────
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)
 
    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self._checked = checked
        self._x = 22 if checked else 2
        self._anim = QPropertyAnimation(self, b"thumb_x")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
 
    @pyqtProperty(int)
    def thumb_x(self):
        return self._x
 
    @thumb_x.setter
    def thumb_x(self, v):
        self._x = v
        self.update()
 
    def isChecked(self):
        return self._checked
 
    def setChecked(self, val):
        if val == self._checked:
            return
        self._checked = val
        target = 22 if val else 2
        self._anim.stop()
        self._anim.setStartValue(self._x)
        self._anim.setEndValue(target)
        self._anim.start()
        self.update()
 
    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)
 
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track_color = QColor("#4caf50") if self._checked else QColor("#555555")
        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 4, 46, 16, 8, 8)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(self._x, 2, 20, 20)
        p.end()
 
 
# ─────────────────────────── SPLASH SCREEN ───────────────────────────
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: #388e3c;")
 
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)
 
        self.label = QLabel(LOGO_HTML)
        self.label.setFont(QFont("Arial", 40, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
 
        self.status_lbl = QLabel("Завантаження...")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #c8e6c9; font-size: 13px; background: transparent;")
        layout.addWidget(self.status_lbl)
 
        layout.addSpacing(5)
 
        self.progress = QProgressBar()
        self.progress.setFixedSize(400, 14)
        self.progress.setTextVisible(False)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2e7d32;
                background-color: #1b5e20;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2e7d32, stop:0.5 #66bb6a, stop:1 #a5d6a7);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress, 0, Qt.AlignCenter)
        self._fade_in()
 
    def _fade_in(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(400)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
 
    def fade_out(self, callback):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(callback)
        anim.start()
        self._fade_out_anim = anim
 
    def set_status(self, text):
        self.status_lbl.setText(text)
 
 
# ─────────────────────────── NICK CONTAINER ───────────────────────────
class NickContainer:
    def __init__(self):
        self.current_nick = "Player"
 
 
# ─────────────────────────── SKIN VIEWER ───────────────────────────
class SkinViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.setStyleSheet("border: 2px solid #4caf50; border-radius: 8px; background: #1e1e1e;")
        self.setAlignment(Qt.AlignCenter)
        self.setText("👤")
        self.setFont(QFont("Segoe UI", 28))
 
    def load_for_nick(self, nick):
        def fetch():
            try:
                url = f"https://minotar.net/helm/{nick}/80"
                data = urllib.request.urlopen(url, timeout=5).read()
                img = QImage()
                img.loadFromData(data)
                pix = QPixmap.fromImage(img).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                QTimer.singleShot(0, lambda: self._set_pixmap(pix))
            except:
                pass
        Thread(target=fetch, daemon=True).start()
 
    def _set_pixmap(self, pix):
        self.setText("")
        self.setPixmap(pix)
 
 
# ─────────────────────────── DISCORD RPC ───────────────────────────
class DiscordRPC:
    APP_ID = "1507482891976966245"
 
    def __init__(self):
        self._rpc = None
        self._connected = False
        self._session_start = None
        self.enabled = True  # керується налаштуванням
 
    def connect(self):
        if not HAS_PYPRESENCE or not self.enabled:
            return
        def _try():
            try:
                self._rpc = Presence(self.APP_ID)
                self._rpc.connect()
                self._connected = True
                self._session_start = int(time.time())
                self.update_menu()
            except:
                pass
        Thread(target=_try, daemon=True).start()
 
    def reconnect_if_needed(self):
        """Підключитися якщо увімкнено і не підключено."""
        if self.enabled and not self._connected:
            self.connect()
 
    def disconnect_rpc(self):
        """Відключитися та очистити статус."""
        self.clear()
 
    def update_menu(self):
        """Show 'In Menu' status."""
        if not self._connected or not self._rpc:
            return
        def _do():
            try:
                self._rpc.update(
                    state="В головному меню",
                    details="G9 Launcher",
                    large_image="logo",
                    large_text="G9 Launcher",
                    start=self._session_start or int(time.time()),
                )
            except:
                pass
        Thread(target=_do, daemon=True).start()
 
    def update_playing(self, version, nick=""):
        """Show playing status with version, nick and elapsed time."""
        if not self._connected or not self._rpc:
            return
        self._game_start = int(time.time())
        details = f"Грає: {version}"
        state = f"Нік: {nick}" if nick else "G9 Launcher"
        def _do():
            try:
                self._rpc.update(
                    state=state,
                    details=details,
                    large_image="logo",
                    large_text="G9 Launcher",
                    small_image="play",
                    small_text=f"Версія: {version}",
                    start=self._game_start,
                )
            except:
                pass
        Thread(target=_do, daemon=True).start()
 
    def update(self, state, details="G9 Launcher"):
        """Legacy method kept for compatibility."""
        if not self._connected or not self._rpc:
            return
        def _do():
            try:
                self._rpc.update(
                    state=state, details=details,
                    large_image="logo", large_text="G9 Launcher",
                    start=self._session_start or int(time.time())
                )
            except:
                pass
        Thread(target=_do, daemon=True).start()
 
    def clear(self):
        if self._connected and self._rpc:
            try:
                self._rpc.clear()
                self._rpc.close()
            except:
                pass
 
 
# ─────────────────────────── JAVA CHECK ───────────────────────────
def check_java():
    try:
        r = _run_hidden(["java", "-version"], capture_output=True, text=True, timeout=5)
        line = (r.stderr or r.stdout).split("\n")[0]
        ver = line.replace("java version", "").replace("openjdk version", "").strip().strip('"').strip("'")
        return True, ver
    except:
        return False, ""
 
 
def show_java_missing_dialog(parent):
    msg = QMessageBox(parent)
    msg.setWindowTitle("Java не знайдено")
    msg.setIcon(QMessageBox.Warning)
    msg.setText(
        "<b>Java не встановлено або не знайдено в PATH.</b><br><br>"
        "Minecraft потребує Java для запуску.<br>"
        "Натисніть <b>Завантажити</b>, щоб перейти на сторінку завантаження Java."
    )
    btn_dl = msg.addButton("☕ Завантажити Java", QMessageBox.AcceptRole)
    msg.addButton("Пропустити", QMessageBox.RejectRole)
    msg.exec_()
    if msg.clickedButton() == btn_dl:
        try:
            os.startfile("https://www.java.com/en/download/")
        except:
            pass
 
 
# ─────────────────────────── VERSIONS ───────────────────────────
# Снапшоти 26.2 (Chaos Cubed) — актуальні Mojang ID
SNAPSHOTS = [
    "26.2 Pre-Release 6 - Snapshot",
    "26.2 Snapshot 8 - Snapshot",
]

# Таблиця відображення: назва у лаунчері → реальний Mojang version ID
DISPLAY_MAP = {
    # Стабільні релізи з новим форматом
    "26.1.2":              ("26.1.2",              None),
    "26.1":                ("26.1",                None),
    # Снапшоти 26.2 — Pre-Releases
    "26.2 Pre-Release 6":  ("26.2-pre-6",          None),
    "26.2 Pre-Release 5":  ("26.2-pre-5",          None),
    "26.2 Pre-Release 4":  ("26.2-pre-4",          None),
    "26.2 Pre-Release 3":  ("26.2-pre-3",          None),
    "26.2 Pre-Release 2":  ("26.2-pre-2",          None),
    "26.2 Pre-Release 1":  ("26.2-pre-1",          None),
    # Снапшоти 26.2 — Snapshots
    "26.2 Snapshot 8":     ("26.2-snapshot-8",     None),
    "26.2 Snapshot 7":     ("26.2-snapshot-7",     None),
    "26.2 Snapshot 6":     ("26.2-snapshot-6",     None),
    "26.2 Snapshot 5":     ("26.2-snapshot-5",     None),
    "26.2 Snapshot 4":     ("26.2-snapshot-4",     None),
    "26.2 Snapshot 3":     ("26.2-snapshot-3",     None),
    "26.2 Snapshot 2":     ("26.2-snapshot-2",     None),
    "26.2 Snapshot 1":     ("26.2-snapshot-1",     None),
}

# ─────────────────────────── NEWS FEED ───────────────────────────
NEWS_FEED_URL = "https://devalfastudios.github.io/G9-Launcher/news.json"

# Fallback static news shown if network is unavailable
NEWS_FALLBACK = [
    {
        "title": "G9 Launcher v1.4 FP 1: Fix Pack 1",
        "summary": "G9 Launcher отримав виправлення у версії 1.4 FP 1 (Fix Pack 1): виправлено критичний баг запуску лаунчера (DISPLAY_MAP not defined), оновлено список снапшотів 26.2 — тепер доступні всі 8 знімків та 6 Pre-Release версій Chaos Cubed, виправлено запуск стабільних версій 26.1 та 26.1.2.",
        "date": "13.06.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "G9 Launcher v1.4: Що нового?",
        "summary": "G9 Launcher отримав нові функції: Зміна стилю на MetroUI, зміна порядку кнопок на лівій боковій панелі, більше варіантів зміни шрифту, можливість показувати активність у Discord, покращення стилю та виправлення багів.",
        "date": "25.05.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "Minecraft 26.1.2",
        "summary": "Minecraft 26.1.2 вже доступний у G9 Launcher. Невеличке технічне оновлення яке вийшло 9 квітня 2026 року.",
        "date": "9.04.2026",
        "image": "",
        "url": "https://minecraft.net/"
    },
    {
        "title": "Нащо ти тут?",
        "summary": "Ти прочитав всі новини — тепер ти у курсі всього!",
        "date": "?",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
]

def fetch_news():
    """Повертає (list, None) — офлайн-режим, дані беруться з NEWS_FALLBACK."""
    return (NEWS_FALLBACK, None)

ALL_VERSIONS = [
    "26.1.2 - Vanilla", "26.1.2 - Forge", "26.1.2 - Fabric", "26.1.2 - NeoForge",
    "26.1 - Vanilla", "26.1 - Forge", "26.1 - Fabric", "26.1 - NeoForge",
    "1.21.11 - Vanilla", "1.21.11 - Forge", "1.21.11 - Fabric", "1.21.11 - NeoForge",
    "1.21.10 - Vanilla", "1.21.10 - Forge", "1.21.10 - Fabric", "1.21.10 - NeoForge",
    "1.21.4 - Vanilla", "1.21.4 - Forge", "1.21.4 - Fabric", "1.21.4 - NeoForge",
    "1.21.3 - Vanilla", "1.21.3 - Forge", "1.21.3 - Fabric", "1.21.3 - NeoForge",
    "1.21.2 - Vanilla", "1.21.2 - Forge", "1.21.2 - Fabric", "1.21.2 - NeoForge",
    "1.21.1 - Vanilla", "1.21.1 - Forge", "1.21.1 - Fabric", "1.21.1 - NeoForge",
    "1.21 - Vanilla", "1.21 - Forge", "1.21 - Fabric", "1.21 - NeoForge",
    "1.20.6 - Vanilla", "1.20.6 - Forge", "1.20.6 - Fabric", "1.20.6 - NeoForge",
    "1.20.4 - Vanilla", "1.20.4 - Forge", "1.20.4 - Fabric", "1.20.4 - NeoForge",
    "1.20.2 - Vanilla", "1.20.2 - Forge", "1.20.2 - Fabric", "1.20.2 - NeoForge",
    "1.20.1 - Vanilla", "1.20.1 - Forge", "1.20.1 - Fabric", "1.20.1 - NeoForge",
    "1.20 - Vanilla", "1.20 - Forge", "1.20 - Fabric", "1.20 - NeoForge",
    "1.19.4 - Vanilla", "1.19.4 - Forge", "1.19.4 - Fabric", "1.19.4 - OptiFine", "1.19.4 - Sodium",
    "1.19.2 - Vanilla", "1.19.2 - Forge", "1.19.2 - Fabric", "1.19.2 - OptiFine",
    "1.19 - Vanilla", "1.19 - Forge", "1.19 - Fabric", "1.19 - OptiFine",
    "1.18.2 - Vanilla", "1.18.2 - Forge", "1.18.2 - Fabric", "1.18.2 - OptiFine",
    "1.17.1 - Vanilla", "1.17.1 - Forge", "1.17.1 - Fabric", "1.17.1 - OptiFine",
    "1.16.5 - Vanilla", "1.16.5 - Forge", "1.16.5 - Fabric", "1.16.5 - OptiFine", "1.16.5 - Forge+OptiFine",
    "1.16 - Vanilla", "1.16 - Forge", "1.16 - Fabric",
    "1.15.2 - Vanilla", "1.15.2 - Forge", "1.15.2 - Fabric", "1.15.2 - OptiFine",
    "1.14.4 - Vanilla", "1.14.4 - Forge", "1.14.4 - Fabric", "1.14.4 - OptiFine",
    "1.13.2 - Vanilla", "1.13.2 - Forge", "1.13.2 - OptiFine",
    "1.12.2 - Vanilla", "1.12.2 - Forge", "1.12.2 - OptiFine", "1.12.2 - Forge+OptiFine",
    "1.8.9 - Vanilla", "1.8.9 - Forge", "1.8.9 - OptiFine",
    "1.7.10 - Vanilla", "1.7.10 - Forge", "1.7.10 - OptiFine",
    "1.6.1 - Vanilla", "1.2 - Vanilla", "1.0 - Vanilla",
]
 
def get_mc_ver_and_loader(selected):
    """Parse display name → (real_mc_version_id, loader_or_None)."""
    # Strip download prefix "✔ " or spaces
    clean = selected.strip().lstrip("✔").strip()
    parts = clean.split(" - ", 1)
    display_ver = parts[0].strip()
    loader_str  = parts[1].strip().lower() if len(parts) > 1 else "vanilla"
    loader = None if loader_str in ("vanilla", "snapshot") else loader_str

    # Check if this display version has a real Mojang ID mapping
    if display_ver in DISPLAY_MAP:
        mapped_id, mapped_loader = DISPLAY_MAP[display_ver]
        return mapped_id, (loader if loader else mapped_loader)

    return display_ver, loader
 
 
def get_downloaded_versions():
    if not HAS_LAUNCHER_LIB:
        return set()
    try:
        vers = minecraft_launcher_lib.utils.get_installed_versions(CONFIG_DIR)
        return {v.get("id", "") for v in vers}
    except:
        return set()
 
 
# ─────────────────────────── MAIN WINDOW ───────────────────────────
class G9Launcher(QMainWindow):
    _news_ready = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.setWindowTitle("G9 Launcher v1.4 FP 1")
        self.setMinimumSize(750, 500)
        self.resize(900, 600)
        self.is_playing = False
        self.nick_dialog = NickContainer()
        self._old_pos = None
        self.discord = DiscordRPC()
        self._base_w = 900
        self._base_h = 600
        self._base_font = 10
 
        # Must be set BEFORE initUI to prevent OS drawing its own titlebar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
 
        self.initUI()
        # Іконка: шукаємо поруч зі скриптом або в поточній папці
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if not os.path.isfile(_icon_path):
            _icon_path = "icon.png"
        _app_icon = QIcon(_icon_path)
        self.setWindowIcon(_app_icon)
        QApplication.instance().setWindowIcon(_app_icon)
        # Фікс іконки на панелі задач Windows — встановлюємо AppUserModelID
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ALFA.G9Launcher.1.5")
        except Exception:
            pass
        self.setStyleSheet(DARK_THEME)
 
        self.load_settings()
        self.refresh_version_combo()
        self.discord.connect()
 
    # ── SCALE UPDATE ──
    def _update_scale(self):
        """Scale base font size proportionally to window size."""
        scale = min(self.width() / self._base_w, self.height() / self._base_h)
        new_font = max(8, int(self._base_font * scale))
        app = QApplication.instance()
        f = app.font()
        f.setPointSize(new_font)
        app.setFont(f)
        self.update()
 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reposition resize grip
        if hasattr(self, "_resize_grip"):
            self._resize_grip.move(self.width() - 16, self.height() - 16)
        self._update_scale()
        # Rescale user bg image on resize
        bg_type_w = getattr(self, "bg_type_combo", None)
        if bg_type_w and bg_type_w.currentText() == "Ваш Фон":
            path = getattr(self, "_bg_path", "")
            if path and os.path.exists(path) and hasattr(self, "_bg_label"):
                pix = QPixmap(path)
                if not pix.isNull():
                    self._bg_label.setPixmap(
                        pix.scaled(self._bg_label.width() or 800,
                                   self._bg_label.height() or 400,
                                   Qt.KeepAspectRatioByExpanding,
                                   Qt.SmoothTransformation))
 
    # ── NAV ──
    def switch_page(self, index):
        if self.stacked_widget.currentIndex() == index:
            return
        self.stacked_widget.setCurrentIndex(index)
        if index == 3:
            self.skin_viewer.load_for_nick(self.nick_dialog.current_nick)
 
    # ── UI BUILD ──
    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
 
        # ── SIDEBAR ──
        side_panel = QWidget()
        side_panel.setFixedWidth(220)
        side_panel.setStyleSheet("background-color: #212121;")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(4)
        side_layout.setContentsMargins(8, 12, 8, 12)
 
        logo = QLabel(LOGO_HTML)
        logo.setFont(QFont("Arial", 20, QFont.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 20pt; background: transparent;")
        self.logo_label = logo
        side_layout.addWidget(logo)
        side_layout.addSpacing(12)
 
        def nav_btn(text, idx):
            b = QPushButton(text)
            b.setMinimumHeight(38)
            b.clicked.connect(lambda: self.switch_page(idx))
            return b
 
        self.btn_settings = nav_btn("⚙ Налаштування", 1)
        self.btn_accounts = nav_btn("👤 Аккаунти", 3)
 
        self.btn_folder = QPushButton("📁 Папка гри")
        self.btn_folder.setMinimumHeight(38)
        self.btn_folder.clicked.connect(lambda: os.startfile(CONFIG_DIR) if os.name == 'nt' else None)
 
        self.btn_screens = QPushButton("🖼 Скріншоти")
        self.btn_screens.setMinimumHeight(38)
        self.btn_screens.clicked.connect(self.open_screenshots)
 
        btn_site = QPushButton("🌐 Сайт")
        btn_site.setMinimumHeight(38)
        btn_site.setToolTip("Відкрити сайт проекту")
        btn_site.clicked.connect(lambda: self._open_url("https://devalfastudios.github.io/G9-Launcher/"))

        self._side_layout = side_layout
        self._btn_site = btn_site

        # ── BUTTONS CONTAINER (fixed position — news hide won't shift them) ──
        self._btns_container = QWidget()
        self._btns_container.setStyleSheet("background: transparent;")
        _btns_vbox = QVBoxLayout(self._btns_container)
        _btns_vbox.setContentsMargins(0, 0, 0, 0)
        _btns_vbox.setSpacing(4)
        for b in [self.btn_settings, self.btn_accounts,
                  self.btn_folder, self.btn_screens, btn_site]:
            _btns_vbox.addWidget(b)
        side_layout.addWidget(self._btns_container)

        # ── NEWS PANEL ──
        self.news_panel = QWidget()
        self.news_panel.setStyleSheet("background: transparent;")
        news_vlayout = QVBoxLayout(self.news_panel)
        news_vlayout.setContentsMargins(0, 8, 0, 0)
        news_vlayout.setSpacing(0)

        news_header_row = QHBoxLayout()
        news_hdr = QLabel("НОВИНИ ГРИ")
        news_hdr.setStyleSheet("color:#888; font-size:11px; font-weight:bold; background:transparent; letter-spacing:1px;")
        news_header_row.addWidget(news_hdr)
        news_header_row.addStretch()
        news_vlayout.addLayout(news_header_row)

        from PyQt5.QtWidgets import QScrollArea
        self.news_scroll = QScrollArea()
        self.news_scroll.setWidgetResizable(True)
        self.news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.news_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.news_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background:#1a1a1a; width:4px; border-radius:2px; }"
            "QScrollBar::handle:vertical { background:#444; border-radius:2px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }"
        )
        self.news_container = QWidget()
        self.news_container.setStyleSheet("background: transparent;")
        self.news_list_layout = QVBoxLayout(self.news_container)
        self.news_list_layout.setSpacing(6)
        self.news_list_layout.setContentsMargins(0, 4, 0, 4)
        self.news_scroll.setWidget(self.news_container)
        news_vlayout.addWidget(self.news_scroll)



        side_layout.addWidget(self.news_panel, 1)  # stretch fills remaining space
        main_layout.addWidget(side_panel)

        # Load news in background
        self._show_news = True
        self._news_ready.connect(self._render_news)
        Thread(target=self._load_news_async, daemon=True).start()
 
        # ── RIGHT AREA ──
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
 
        # Title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background-color: #212121; border-bottom: 1px solid #388e3c;")
        t_layout = QHBoxLayout(self.title_bar)
        t_layout.setContentsMargins(15, 0, 10, 0)
 
        btn_minimize = QPushButton("—")
        btn_minimize.setObjectName("TitleBarBtn")
        btn_minimize.setFixedSize(30, 30)
        btn_minimize.setStyleSheet("QPushButton#TitleBarBtn { background-color: transparent; border: none; font-size: 18px; color: #888; border-radius: 4px; } QPushButton#TitleBarBtn:hover { background-color: #3a3a3a; color: white; }")
        btn_minimize.clicked.connect(self._animate_minimize)
 
        btn_close = QPushButton("✕")
        btn_close.setObjectName("TitleBarClose")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("QPushButton#TitleBarClose { background-color: transparent; border: none; font-size: 18px; color: #888; border-radius: 4px; } QPushButton#TitleBarClose:hover { background-color: #c0392b; color: white; }")
        btn_close.clicked.connect(self._animate_close)
 
        t_layout.addStretch()
        t_layout.addWidget(btn_minimize)
        t_layout.addWidget(btn_close)
 
        right_layout.addWidget(self.title_bar)
 
        self.stacked_widget = QStackedWidget()
 
        # ── Page 0: Home ──
        self.home_page = QWidget()
        self.home_page.setObjectName("home_page")
        home_layout = QVBoxLayout(self.home_page)
        home_layout.setContentsMargins(0, 0, 0, 0)
        home_layout.setSpacing(0)

        # ── Static photo background ──
        self._bg_label = QLabel()
        self._bg_label.setScaledContents(True)
        self._bg_label.setStyleSheet("background: #1a1a1a;")
        self._bg_url = "https://ru-minecraft.ru/uploads/posts/2026-03/1774009280_1600px-tiny_takeover_key_art-1.jpg"  # ← пряме посилання на фон
        self._load_bg_from_url(self._bg_url)
        home_layout.addWidget(self._bg_label, 1)
 
        bottom_panel = QWidget()
        bottom_panel.setStyleSheet("background-color: #2b2b2b; border-top: 2px solid #4caf50;")
        self.bottom_bar = bottom_panel
        bottom_layout = QVBoxLayout(bottom_panel)
 
        self.launch_progress = QProgressBar()
        self.launch_progress.setFixedHeight(5)
        self.launch_progress.setTextVisible(False)
        self.launch_progress.setStyleSheet("""
            QProgressBar { background: #1a1a1a; border: none; border-radius: 2px; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2e7d32, stop:0.6 #4caf50, stop:1 #81c784);
                border-radius: 2px;
            }
        """)
        self.launch_progress.hide()
        bottom_layout.addWidget(self.launch_progress)
 
        controls = QHBoxLayout()
 
        self.version_combo = QComboBox()
        self.version_combo.setMaxVisibleItems(12)
        self.version_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.version_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.version_combo.setMinimumHeight(40)
        self.version_combo.setMinimumWidth(220)
        self.version_combo.currentIndexChanged.connect(self._on_version_changed)
 
        self.btn_nick = QPushButton("Нік: Player")
        self.btn_nick.setMinimumHeight(40)
        self.btn_nick.clicked.connect(lambda: self.switch_page(3))
 
        self.btn_play = QPushButton("▶  Грати")
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.setMinimumHeight(50)
        self.btn_play.setMinimumWidth(200)
        self.btn_play.clicked.connect(self.toggle_play)
 
        controls.addWidget(self.version_combo)
        controls.addWidget(self.btn_nick)
        controls.addStretch()
        controls.addWidget(self.btn_play)
        bottom_layout.addLayout(controls)
 
        home_layout.addWidget(bottom_panel)
        self.stacked_widget.addWidget(self.home_page)   # index 0
 
        # ── Page 1: Settings ──
        self.settings_page = QWidget()
        self.init_settings_page()
        self.stacked_widget.addWidget(self.settings_page)  # index 1
 
        # ── Page 2: About ──
        self.about_page = QWidget()
        self.init_about_page()
        self.stacked_widget.addWidget(self.about_page)     # index 2
 
        # ── Page 3: Accounts ──
        self.accounts_page = QWidget()
        self.init_accounts_page()
        self.stacked_widget.addWidget(self.accounts_page)  # index 3
 

        right_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(right_area)
 
        # ── Resize grip (bottom-right of whole window) ──
        self._resize_grip = ResizeGrip(self)
        self._resize_grip.move(self.width() - 16, self.height() - 16)
        self._resize_grip.raise_()
 
        self._populate_version_combo()
 
    # ── VERSION COMBO ──
    def _populate_version_combo(self):
        downloaded = get_downloaded_versions()
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        show_snaps = getattr(self, "_show_snapshots", True)
        versions_to_show = (SNAPSHOTS if show_snaps else []) + ALL_VERSIONS
        for v in versions_to_show:
            mc_ver, _ = get_mc_ver_and_loader(v)
            is_dl = mc_ver in downloaded
            prefix = "✔ " if is_dl else "   "
            self.version_combo.addItem(prefix + v)
        self.version_combo.blockSignals(False)
 
    def refresh_version_combo(self):
        current = self._current_version_text()
        self._populate_version_combo()
        for i in range(self.version_combo.count()):
            if self.version_combo.itemText(i).strip().lstrip("✔").strip() == current:
                self.version_combo.setCurrentIndex(i)
                break
 
    def _current_version_text(self):
        t = self.version_combo.currentText()
        return t.strip().lstrip("✔").strip()
 
    def _on_version_changed(self, idx):
        pass
 
    # ── SETTINGS PAGE ──
    def init_settings_page(self):
        page_layout = QVBoxLayout(self.settings_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
 
        # ── Header bar ──
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background:#1a1a1a; border-bottom:1px solid #333;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(lambda: self.switch_page(0))
        title_lbl = QLabel("Налаштування")
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_lbl.setStyleSheet("color: #4caf50; background: transparent;")
        hdr_lay.addWidget(btn_back)
        hdr_lay.addSpacing(16)
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()
        page_layout.addWidget(hdr)
 
        # ── Tab widget ──
        self._settings_tabs = QTabWidget()
        self._settings_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #1e1e1e;
                color: #888;
                padding: 10px 18px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 12px;
                font-weight: bold;
                min-width: 90px;
            }
            QTabBar::tab:selected {
                color: #4caf50;
                border-bottom: 2px solid #4caf50;
                background: #2b2b2b;
            }
            QTabBar::tab:hover:!selected {
                color: #ccc;
                background: #252525;
            }
        """)
        page_layout.addWidget(self._settings_tabs)
 
        GRP = """
            QGroupBox { font-weight: bold; font-size: 11px; letter-spacing: 1px;
                        border: 1px solid #3a3a3a; border-radius: 8px;
                        margin-top: 10px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #aaa; }
        """
 
        def scrolled_tab():
            outer = QWidget()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            inner = QWidget()
            lay = QVBoxLayout(inner)
            lay.setContentsMargins(24, 18, 24, 18)
            lay.setSpacing(14)
            scroll.setWidget(inner)
            ol = QVBoxLayout(outer)
            ol.setContentsMargins(0, 0, 0, 0)
            ol.addWidget(scroll)
            return outer, lay
 
        # ══════════════════════════════════════════
        # TAB 1 — ГРА
        # ══════════════════════════════════════════
        tab_game, lay_game = scrolled_tab()
 
        sys_ram_gb = int(psutil.virtual_memory().total / (1024**3)) if psutil else 8
 
        mem_box = QGroupBox("ПАМ'ЯТЬ")
        mem_box.setStyleSheet(GRP)
        mem_layout = QVBoxLayout(mem_box)
        ram_info = QHBoxLayout()
        ram_info.addWidget(QLabel("Виділена ОЗУ"))
        ram_info.addStretch()
        avail = QLabel(f"Доступно: {sys_ram_gb} ГБ")
        avail.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
        ram_info.addWidget(avail)
        mem_layout.addLayout(ram_info)
        self.ram_slider = NoScrollSlider(Qt.Horizontal)
        self.ram_slider.setMinimum(1)
        self.ram_slider.setMaximum(min(32, sys_ram_gb))
        self.ram_slider.setValue(2)
        self.ram_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #3a3a3a; border-radius: 2px; }
            QSlider::handle:horizontal { background: #4caf50; border: none; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::sub-page:horizontal { background: #4caf50; border-radius: 2px; }
        """)
        self.ram_label = QLabel("2 ГБ")
        self.ram_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 13px; background: transparent;")
        self.ram_slider.valueChanged.connect(lambda v: self.ram_label.setText(f"{v} ГБ"))
        slider_row = QHBoxLayout()
        slider_row.addWidget(self.ram_slider)
        slider_row.addWidget(self.ram_label)
        mem_layout.addLayout(slider_row)
        lay_game.addWidget(mem_box)
 
        threads_count = psutil.cpu_count(logical=True) if psutil else 4
        cpu_box = QGroupBox("ПРОЦЕСОР")
        cpu_box.setStyleSheet(GRP)
        cpu_layout = QVBoxLayout(cpu_box)
        cpu_layout.addWidget(QLabel("Кількість ядер/потоків"))
        self.core_combo = NoScrollCombo()
        self.core_combo.addItem("Авто (рекомендовано)")
        for i in range(1, threads_count + 1):
            self.core_combo.addItem(f"{i} Ядер/Потоків")
        cpu_layout.addWidget(self.core_combo)
        lay_game.addWidget(cpu_box)
 
        # ─ GameBooster ─
        BOOSTER_GRP = """
            QGroupBox { font-weight: bold; font-size: 11px; letter-spacing: 1px;
                        border: 2px solid #1565c0; border-radius: 8px;
                        margin-top: 10px; padding: 12px;
                        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                            stop:0 #1a237e22, stop:1 #0d47a122); }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #64b5f6; }
        """
        booster_box = QGroupBox("🚀 AI GAMEBOOSTER")
        booster_box.setStyleSheet(BOOSTER_GRP)
        booster_vbox = QVBoxLayout(booster_box)
        booster_desc = QLabel("Автоматично оптимізує параметри запуску\nна основі характеристик вашого ПК (незабаром)")
        booster_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        booster_vbox.addWidget(booster_desc)
        row_booster = QHBoxLayout()
        lbl_booster_name = QLabel("Увімкнути AI GameBooster")
        row_booster.addWidget(lbl_booster_name)
        soon_lbl = QLabel("  СКОРО")
        soon_lbl.setStyleSheet("color: #64b5f6; font-size: 10px; font-weight: bold; background: transparent; border: 1px solid #1565c0; border-radius: 3px; padding: 1px 4px;")
        row_booster.addWidget(soon_lbl)
        row_booster.addStretch()
        self.chk_booster = ToggleSwitch(checked=False)
        self.chk_booster.setEnabled(False)
        self.chk_booster.setStyleSheet("opacity: 0.4;")
        row_booster.addWidget(self.chk_booster)
        booster_vbox.addLayout(row_booster)
        lay_game.addWidget(booster_box)
 
        gfx_box_g = QGroupBox("ГРАФІКА ТА ВІКНО")
        gfx_box_g.setStyleSheet(GRP)
        gfx_layout_g = QVBoxLayout(gfx_box_g)
        gfx_layout_g.addWidget(QLabel("Розмір вікна Minecraft:"))
        win_row_g = QHBoxLayout()
        self.win_w = QLineEdit("1280")
        self.win_h = QLineEdit("720")
        for f in [self.win_w, self.win_h]:
            f.setFixedWidth(80)
            f.setStyleSheet("background: #333; color: white; border: 1px solid #555; border-radius: 4px; padding: 5px;")
        win_row_g.addWidget(self.win_w)
        win_row_g.addWidget(QLabel("x"))
        win_row_g.addWidget(self.win_h)
        win_row_g.addStretch()
        gfx_layout_g.addLayout(win_row_g)
        win_toggle_row_g = QHBoxLayout()
        win_toggle_row_g.addWidget(QLabel("Відкрити у вікні"))
        win_toggle_row_g.addStretch()
        self.chk_windowed = ToggleSwitch(checked=True)
        win_toggle_row_g.addWidget(self.chk_windowed)
        gfx_layout_g.addLayout(win_toggle_row_g)
        lay_game.addWidget(gfx_box_g)
 
        lay_game.addStretch()
        self._settings_tabs.addTab(tab_game, "🎮  Гра")
 
        # ══════════════════════════════════════════
        # TAB 2 — JAVA
        # ══════════════════════════════════════════
        tab_java, lay_java = scrolled_tab()
 
        java_ok, java_ver = check_java()
        java_path = shutil.which("java") or "/usr/bin/java"
 
        java_box = QGroupBox("ДЖАВА")
        java_box.setStyleSheet(GRP)
        java_layout = QVBoxLayout(java_box)
        java_status = QLabel("☕ " + (java_ver if java_ok else "❌ Не знайдено!"))
        java_status.setStyleSheet(f"color: {'#4caf50' if java_ok else '#ef5350'}; font-size: 12px; background: transparent;")
        java_layout.addWidget(java_status)
        path_lbl = QLabel("Шлях до Java:")
        path_lbl.setStyleSheet("color: #ccc; font-size: 11px; background: transparent;")
        java_layout.addWidget(path_lbl)
        java_path_row = QHBoxLayout()
        self.java_path_lbl = QLabel(java_path)
        self.java_path_lbl.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
        self.java_path_lbl.setWordWrap(True)
        btn_java_change = QPushButton("Змінити")
        btn_java_change.setFixedWidth(80)
        btn_java_change.clicked.connect(self.change_java_path)
        java_path_row.addWidget(self.java_path_lbl)
        java_path_row.addWidget(btn_java_change)
        java_layout.addLayout(java_path_row)
        btn_dl_java = QPushButton("☕ Завантажити Java")
        btn_dl_java.setStyleSheet("background: #e65100; color: white;")
        btn_dl_java.clicked.connect(lambda: os.startfile("https://www.java.com/en/download/"))
        java_layout.addWidget(btn_dl_java)
        btn_java_reset = QPushButton("Скинути шлях Java")
        btn_java_reset.clicked.connect(lambda: self.java_path_lbl.setText(shutil.which("java") or "/usr/bin/java"))
        java_layout.addWidget(btn_java_reset)
        jvm_args_lbl = QLabel("Аргументи запуску JVM:")
        jvm_args_lbl.setStyleSheet("color: #ccc; font-size: 11px; background: transparent;")
        java_layout.addWidget(jvm_args_lbl)
        self.jvm_args_input = QLineEdit()
        self.jvm_args_input.setPlaceholderText("-Xss1M -XX:+UseZGC ...")
        self.jvm_args_input.setStyleSheet("background: #333; color: white; border: 1px solid #555; border-radius: 4px; padding: 5px;")
        java_layout.addWidget(self.jvm_args_input)
        lay_java.addWidget(java_box)
        lay_java.addStretch()
        self._settings_tabs.addTab(tab_java, "☕  Java")
 
        # ══════════════════════════════════════════
        # TAB 3 — КАСТОМІЗАЦІЯ (ВИГЛЯД)
        # ══════════════════════════════════════════
        tab_custom, lay_custom = scrolled_tab()
 
        custom_box = QGroupBox("КАСТОМІЗАЦІЯ")
        custom_box.setStyleSheet(GRP)
        custom_vbox = QVBoxLayout(custom_box)

        # ── Background selector ──
        bg_lbl = QLabel("Тип фону:")
        bg_lbl.setStyleSheet("color: #ccc; font-size: 12px; background: transparent; margin-top: 4px;")
        custom_vbox.addWidget(bg_lbl)

        self.bg_type_combo = NoScrollCombo()
        self.bg_type_combo.addItems(["Фон Колір", "Ваш Фон"])
        self.bg_type_combo.setFixedWidth(200)
        custom_vbox.addWidget(self.bg_type_combo)

        # Note for "Фон Колір": uses the "Фон" color from the palette section below
        self._bg_color_hint = QLabel("🎨 Колір задається кнопкою «Фон» у кольоровій схемі нижче")
        self._bg_color_hint.setStyleSheet("color:#888; font-size:11px; background:transparent; padding:4px 0;")
        self._bg_color_hint.setWordWrap(True)
        custom_vbox.addWidget(self._bg_color_hint)

        # Custom file bg row
        self._bg_file_row = QWidget()
        _bf_lay = QHBoxLayout(self._bg_file_row)
        _bf_lay.setContentsMargins(0, 4, 0, 0)
        _bf_lay.setSpacing(6)
        btn_bg_file = QPushButton("🖼 Вибрати файл")
        btn_bg_file.setStyleSheet("background:#333; color:#ccc; border:1px solid #555; padding:8px; border-radius:6px;")
        btn_bg_file.clicked.connect(self.change_background)
        btn_bg_reset = QPushButton("✕ Скинути фон")
        btn_bg_reset.setStyleSheet("background:#333; color:#ccc; border:1px solid #555; padding:8px; border-radius:6px;")
        btn_bg_reset.clicked.connect(self.reset_background)
        self._bg_file_label = QLabel("Не вибрано")
        self._bg_file_label.setStyleSheet("color:#666; font-size:11px; background:transparent;")
        self._bg_file_label.setWordWrap(True)
        _bf_lay.addWidget(btn_bg_file)
        _bf_lay.addWidget(btn_bg_reset)
        _bf_lay.addWidget(self._bg_file_label, 1)
        custom_vbox.addWidget(self._bg_file_row)
        self._bg_file_row.hide()

        def on_bg_type_changed(text):
            self._bg_color_hint.setVisible(text == "Фон Колір")
            self._bg_file_row.setVisible(text == "Ваш Фон")
            self._apply_bg_type()
            self.save_settings()
        self.bg_type_combo.currentTextChanged.connect(on_bg_type_changed)
        # Init visibility
        self._bg_color_hint.setVisible(True)
 
        palette_lbl = QLabel("Кольорова схема:")
        palette_lbl.setStyleSheet("color: #ccc; font-size: 12px; background: transparent; margin-top: 6px;")
        custom_vbox.addWidget(palette_lbl)
 
        palette_row = QHBoxLayout()
        palette_row.setSpacing(10)
        BTN_STYLE = "font-size:11px; padding:4px 8px; border-radius:4px;"
        RST_STYLE = "font-size:11px; padding:4px 6px; border-radius:4px; background:#2a2a2a; color:#888; border:1px solid #444; font-weight:normal;"
 
        def make_color_col(label_text, attr, default_color):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignTop)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color:#aaa; font-size:11px; background:transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            preview = QLabel()
            preview.setFixedSize(52, 28)
            cur = getattr(self, attr, default_color)
            preview.setStyleSheet(f"background:{cur}; border-radius:5px; border:1px solid #555;")
            setattr(self, attr + "_preview", preview)
            btn_pick = QPushButton("Змінити")
            btn_pick.setFixedHeight(28)
            btn_pick.setStyleSheet(BTN_STYLE)
            btn_rst = QPushButton("↺")
            btn_rst.setFixedHeight(28)
            btn_rst.setToolTip(f"Скинути до {default_color}")
            btn_rst.setStyleSheet(RST_STYLE)
            def pick(a=attr, p=preview, d=default_color):
                c = QColorDialog.getColor(QColor(getattr(self, a, d)), self, "Вибір кольору")
                if c.isValid():
                    setattr(self, a, c.name())
                    p.setStyleSheet(f"background:{c.name()}; border-radius:5px; border:1px solid #555;")
                    self._apply_palette(); self.save_settings()
            def reset(a=attr, p=preview, d=default_color):
                setattr(self, a, d)
                p.setStyleSheet(f"background:{d}; border-radius:5px; border:1px solid #555;")
                self._apply_palette(); self.save_settings()
            btn_pick.clicked.connect(lambda _=None, _p=pick: _p())
            btn_rst.clicked.connect(lambda _=None, _r=reset: _r())
            btns_row = QHBoxLayout()
            btns_row.setSpacing(4)
            btns_row.addWidget(btn_pick, 1)
            btns_row.addWidget(btn_rst)
            col.addWidget(lbl)
            col.addWidget(preview, 0, Qt.AlignCenter)
            col.addLayout(btns_row)
            return col
 
        palette_row.addLayout(make_color_col("Акцент",  "_color_accent",  "#4caf50"))
        palette_row.addSpacing(8)
        palette_row.addLayout(make_color_col("Сайдбар", "_color_sidebar", "#212121"))
        palette_row.addSpacing(8)
        palette_row.addLayout(make_color_col("Фон",     "_color_bg",      "#2b2b2b"))
        palette_row.addSpacing(8)
        palette_row.addLayout(make_color_col("Текст",   "_color_text",    "#ffffff"))
        palette_row.addSpacing(8)
        palette_row.addLayout(make_color_col("Заголовок", "_color_titlebar", "#212121"))
        palette_row.addStretch()
        custom_vbox.addLayout(palette_row)
 

        lay_custom.addWidget(custom_box)

        # ── Панель: видимість + порядок + новини + знімки ──
        from PyQt5.QtWidgets import QListWidget, QAbstractItemView
        panel_box = QGroupBox("БОКОВА ПАНЕЛЬ ТА КОНТЕНТ")
        panel_box.setStyleSheet(GRP)
        panel_vbox = QVBoxLayout(panel_box)

        # Visibility toggles
        vis_lbl = QLabel("Видимість кнопок:")
        vis_lbl.setStyleSheet("color:#ccc; font-size:11px; font-weight:bold; background:transparent; margin-top:4px;")
        panel_vbox.addWidget(vis_lbl)

        for (label_txt, attr, btn_attr, extra_fn) in [
            ("Показувати «Аккаунти»",  "chk_show_accounts_btn", "btn_accounts",  None),
            ("Показувати «Папка гри»", "chk_show_folder_btn",   "btn_folder",    None),
            ("Показувати «Скріншоти»", "chk_show_screens_btn",  "btn_screens",   None),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_txt))
            row.addStretch()
            chk = ToggleSwitch(checked=True)
            def make_vis_fn(b_attr, ex):
                def fn(val):
                    b = getattr(self, b_attr, None)
                    if b: b.setVisible(val)
                    if ex: ex(val)
                    self.save_settings()
                return fn
            chk.toggled.connect(make_vis_fn(btn_attr, extra_fn))
            setattr(self, attr, chk)
            row.addWidget(chk)
            panel_vbox.addLayout(row)

        # News toggle
        row_news = QHBoxLayout()
        row_news.addWidget(QLabel("Показувати новини гри"))
        row_news.addStretch()
        self.chk_show_news = ToggleSwitch(checked=True)
        def toggle_news(val):
            self._show_news = val
            if hasattr(self, "news_panel"):
                self.news_panel.setVisible(val)
            self.save_settings()
        self.chk_show_news.toggled.connect(toggle_news)
        row_news.addWidget(self.chk_show_news)
        panel_vbox.addLayout(row_news)

        # Snapshots toggle
        row_snap = QHBoxLayout()
        row_snap.addWidget(QLabel("Показувати знімки (Snapshots)"))
        row_snap.addStretch()
        self.chk_show_snapshots = ToggleSwitch(checked=True)
        def toggle_snapshots(val):
            self._show_snapshots = val
            self.refresh_version_combo()
            self.save_settings()
        self.chk_show_snapshots.toggled.connect(toggle_snapshots)
        row_snap.addWidget(self.chk_show_snapshots)
        panel_vbox.addLayout(row_snap)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#333; background:#333; margin: 4px 0;")
        panel_vbox.addWidget(sep)

        # Order list
        ord_lbl = QLabel("Порядок кнопок (перетягуйте):")
        ord_lbl.setStyleSheet("color:#ccc; font-size:11px; font-weight:bold; background:transparent; margin-top:4px;")
        panel_vbox.addWidget(ord_lbl)

        self.sidebar_order_list = QListWidget()
        self.sidebar_order_list.setFixedHeight(150)
        self.sidebar_order_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.sidebar_order_list.setDefaultDropAction(Qt.MoveAction)
        self.sidebar_order_list.setStyleSheet(
            "QListWidget { background: #1e1e1e; border: 1px solid #444; border-radius:4px; color:#eee; }"
            "QListWidget::item { padding: 6px 8px; }"
            "QListWidget::item:selected { background: #2e7d32; }"
        )
        self._sidebar_button_order = getattr(self, "_sidebar_button_order",
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти", "🌐 Сайт"])
        for name in self._sidebar_button_order:
            self.sidebar_order_list.addItem(name)

        def on_sidebar_order_changed():
            new_order = [self.sidebar_order_list.item(i).text()
                         for i in range(self.sidebar_order_list.count())]
            self._sidebar_button_order = new_order
            self._apply_sidebar_order()
            self.save_settings()
        self.sidebar_order_list.model().rowsMoved.connect(lambda *_: on_sidebar_order_changed())
        panel_vbox.addWidget(self.sidebar_order_list)

        lay_custom.addWidget(panel_box)

        # ── Шрифт та текст ──
        font_box = QGroupBox("ШРИФТ ТА РОЗМІР ТЕКСТУ")
        font_box.setStyleSheet(GRP)
        font_vbox = QVBoxLayout(font_box)
 
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Шрифт інтерфейсу:"))
        font_row.addStretch()
        self.font_combo = NoScrollCombo()
        self.font_combo.addItems([
            "Segoe UI", "Arial", "Calibri", "Consolas", "Tahoma", "Verdana", "Roboto",
            "Minecraft Ten", "Press Start 2P", "VT323", "Courier New", "Lucida Console", "Fixedsys"
        ])
        self.font_combo.setFixedWidth(160)
        def on_font_changed(f):
            if getattr(self, "_applying_palette", False): return
            self._ui_font_family = f
            QTimer.singleShot(0, self._apply_palette)
            QTimer.singleShot(50, self.save_settings)
        self.font_combo.currentTextChanged.connect(on_font_changed)
        font_row.addWidget(self.font_combo)
        font_vbox.addLayout(font_row)
 
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Розмір тексту:"))
        size_row.addStretch()
        self.font_size_slider = NoScrollSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(18)
        self.font_size_slider.setValue(10)
        self.font_size_slider.setFixedWidth(140)
        self.font_size_slider.setStyleSheet("""
            QSlider::groove:horizontal { height:4px; background:#3a3a3a; border-radius:2px; }
            QSlider::handle:horizontal { background:#4caf50; border:none; width:14px; height:14px; margin:-5px 0; border-radius:7px; }
            QSlider::sub-page:horizontal { background:#4caf50; border-radius:2px; }
        """)
        self.font_size_lbl = QLabel("10 pt")
        self.font_size_lbl.setStyleSheet("color:#4caf50; font-weight:bold; min-width:36px; background:transparent;")
        def on_font_size(v):
            if getattr(self, "_applying_palette", False): return
            self.font_size_lbl.setText(f"{v} pt")
            self._ui_font_size = v
            QTimer.singleShot(0, self._apply_palette)
            QTimer.singleShot(50, self.save_settings)
        self.font_size_slider.valueChanged.connect(on_font_size)
        size_row.addWidget(self.font_size_slider)
        size_row.addWidget(self.font_size_lbl)
        font_vbox.addLayout(size_row)
        lay_custom.addWidget(font_box)

        # ── UI Style ──
        style_box = QGroupBox("СТИЛЬ ІНТЕРФЕЙСУ")
        style_box.setStyleSheet(GRP)
        style_vbox = QVBoxLayout(style_box)
        style_desc = QLabel("Вибір теми оформлення вікна лаунчера.")
        style_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        style_vbox.addWidget(style_desc)
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Стиль:"))
        style_row.addStretch()
        self.ui_style_combo = NoScrollCombo()
        self.ui_style_combo.addItems(["G9 UI", "MetroUI"])
        self.ui_style_combo.setFixedWidth(200)
        def on_ui_style(s):
            self._ui_style = s
            self._apply_ui_style()
            self.save_settings()
        self.ui_style_combo.currentTextChanged.connect(on_ui_style)
        style_row.addWidget(self.ui_style_combo)
        style_vbox.addLayout(style_row)
        lay_custom.addWidget(style_box)

        # ─ Кнопка скидання всього ─
        reset_all_box = QGroupBox("СКИДАННЯ")
        reset_all_box.setStyleSheet(GRP)
        reset_all_vbox = QVBoxLayout(reset_all_box)
        reset_desc = QLabel("Скинути всі налаштування вигляду та лаунчера до стандартних значень.")
        reset_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        reset_desc.setWordWrap(True)
        reset_all_vbox.addWidget(reset_desc)
        btn_reset_all = QPushButton("🗑  Скинути все до стандартних")
        btn_reset_all.setStyleSheet(
            "background: #c62828; color: white; border: 2px solid #b71c1c; "
            "padding: 8px; border-radius: 6px; font-weight: bold;"
        )
        btn_reset_all.clicked.connect(self._confirm_reset_all)
        reset_all_vbox.addWidget(btn_reset_all)
        lay_custom.addWidget(reset_all_box)

        lay_custom.addStretch()
        self._settings_tabs.addTab(tab_custom, "🎨  Вигляд")
 
        # ══════════════════════════════════════════
        # TAB 4 — ЗАПУСК
        # ══════════════════════════════════════════
        tab_beh, lay_beh = scrolled_tab()
 
        behavior_box = QGroupBox("ЗАПУСК ЛАУНЧЕРА")
        behavior_box.setStyleSheet(GRP)
        behavior_vbox = QVBoxLayout(behavior_box)
 
        row_hide = QHBoxLayout()
        row_hide.addWidget(QLabel("Сховати лаунчер під час гри"))
        row_hide.addStretch()
        self.chk_hide_on_launch = ToggleSwitch(checked=True)
        row_hide.addWidget(self.chk_hide_on_launch)
        behavior_vbox.addLayout(row_hide)

        row_autostart = QHBoxLayout()
        row_autostart.addWidget(QLabel("Запускати лаунчер при старті Windows"))
        row_autostart.addStretch()
        self.chk_autostart = ToggleSwitch(checked=self._get_autostart_enabled())
        def toggle_autostart(val):
            ok = self._set_autostart(val)
            if not ok:
                QMessageBox.warning(self, "Автозапуск",
                    "Не вдалося змінити автозапуск.\nСпробуйте від імені адміністратора.")
                self.chk_autostart.setChecked(not val)
        self.chk_autostart.toggled.connect(toggle_autostart)
        row_autostart.addWidget(self.chk_autostart)
        behavior_vbox.addLayout(row_autostart)

        row_autoupd = QHBoxLayout()
        row_autoupd.addWidget(QLabel("Автоперевірка оновлень при запуску"))
        row_autoupd.addStretch()
        self.chk_auto_update = ToggleSwitch(checked=True)
        self.chk_auto_update.toggled.connect(self.save_settings)
        row_autoupd.addWidget(self.chk_auto_update)
        behavior_vbox.addLayout(row_autoupd)

        row_con = QHBoxLayout()
        row_con.addWidget(QLabel("Консоль при запуску"))
        row_con.addStretch()
        self.chk_console = ToggleSwitch(checked=False)
        row_con.addWidget(self.chk_console)
        behavior_vbox.addLayout(row_con)
 
        row_con_err = QHBoxLayout()
        row_con_err.addWidget(QLabel("Консоль при помилці"))
        row_con_err.addStretch()
        self.chk_console_err = ToggleSwitch(checked=True)
        row_con_err.addWidget(self.chk_console_err)
        behavior_vbox.addLayout(row_con_err)
 
        lay_beh.addWidget(behavior_box)

        # ─ Discord RPC ─
        discord_box = QGroupBox("DISCORD")
        discord_box.setStyleSheet(GRP)
        discord_vbox = QVBoxLayout(discord_box)

        disc_desc = QLabel("Показувати активність у Discord (Rich Presence)")
        disc_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        discord_vbox.addWidget(disc_desc)

        row_discord = QHBoxLayout()
        row_discord.addWidget(QLabel("Активність у Discord"))
        row_discord.addStretch()
        self.chk_discord_rpc = ToggleSwitch(checked=True)
        def toggle_discord_rpc(val):
            self.discord.enabled = val
            self.save_settings()
            if val:
                # Need restart to connect — show dialog
                reply = QMessageBox.question(
                    self, "Перезапуск лаунчера",
                    "Для увімкнення Discord активності потрібно перезапустити лаунчер.\nПерезапустити зараз?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    import subprocess, sys
                    subprocess.Popen([sys.executable] + sys.argv)
                    self.close()
            else:
                self.discord.disconnect_rpc()
        self.chk_discord_rpc.toggled.connect(toggle_discord_rpc)
        if not HAS_PYPRESENCE:
            self.chk_discord_rpc.setEnabled(False)
            self.chk_discord_rpc.setToolTip("pypresence не знайдено")
        row_discord.addWidget(self.chk_discord_rpc)
        discord_vbox.addLayout(row_discord)



        lay_beh.addWidget(discord_box)
        lay_beh.addStretch()
        self._settings_tabs.addTab(tab_beh, "🚀  Запуск")
 
        # ══════════════════════════════════════════
        # TAB 6 — ПРО ПРОГРАМУ
        # ══════════════════════════════════════════
        tab_about, lay_about = scrolled_tab()
 
        # ── Header banner ──
        banner = QWidget()
        banner.setFixedHeight(110)
        banner.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #1b5e20, stop:0.5 #2e7d32, stop:1 #388e3c);
            border-radius: 10px;
        """)
        ban_lay = QVBoxLayout(banner)
        ban_lay.setAlignment(Qt.AlignCenter)
        logo_lbl2 = QLabel(LOGO_HTML)
        logo_lbl2.setFont(QFont("Arial", 26, QFont.Bold))
        logo_lbl2.setAlignment(Qt.AlignCenter)
        logo_lbl2.setStyleSheet("font-size: 26pt; background: transparent;")
        ban_lay.addWidget(logo_lbl2)
        tagline2 = QLabel("Твій шлях до Minecraft")
        tagline2.setAlignment(Qt.AlignCenter)
        tagline2.setStyleSheet("color: #a5d6a7; font-size: 12px; background: transparent;")
        ban_lay.addWidget(tagline2)
        lay_about.addWidget(banner)
 
        info_box = QGroupBox("ІНФОРМАЦІЯ")
        info_box.setStyleSheet(GRP)
        info_vbox = QVBoxLayout(info_box)
        info_vbox.setSpacing(10)
 
        def _info_row2(key, val, color="#4caf50"):
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
            v = QLabel(val)
            v.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; background: transparent;")
            row.addWidget(k)
            row.addStretch()
            row.addWidget(v)
            return row
 
        info_vbox.addLayout(_info_row2("Версія лаунчера:", "1.4 FP 1 (Fix Pack 1)"))
        info_vbox.addLayout(_info_row2("Розробник:", "ALFA Studios", "#4da6ff"))
 
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #3a3a3a;")
        info_vbox.addWidget(sep2)
 
        # Specs expandable
        btn_specs2 = QPushButton("▶  Характеристики пристрою")
        btn_specs2.setCheckable(True)
        btn_specs2.setChecked(False)
        btn_specs2.setStyleSheet("""
            QPushButton { text-align:left; padding:8px 12px; background:#252525; color:#888;
                          border:1px solid #383838; border-radius:6px; font-size:12px; font-weight:normal; }
            QPushButton:checked { background:#1e2a1e; color:#9ccc65; border:1px solid #4caf50; }
            QPushButton:hover { background:#2e2e2e; }
        """)
        from PyQt5.QtWidgets import QTextEdit as _QTE2
        specs_text2 = _QTE2()
        specs_text2.setReadOnly(True)
        specs_text2.setVisible(False)
        specs_text2.setMaximumHeight(200)
        specs_text2.setStyleSheet("""
            QTextEdit { background:#1a1a1a; color:#ccc; border:1px solid #333;
                        border-top:none; border-radius:0 0 6px 6px;
                        font-family:Consolas,monospace; font-size:11px; padding:8px; }
        """)
        try:
            import multiprocessing, socket
            lines = []
            cpu_name = platform.processor() or platform.machine() or "N/A"
            try:
                freq = psutil.cpu_freq()
                freq_s = f" @ {freq.max/1000:.1f} GHz" if freq else ""
            except: freq_s = ""
            lines.append(f"CPU:        {cpu_name}{freq_s}")
            lines.append(f"Ядра:       {multiprocessing.cpu_count()}")
            if psutil:
                vm = psutil.virtual_memory()
                lines.append(f"ОЗУ:        {vm.total/1024**3:.1f} ГБ  (зайнято {vm.percent:.0f}%)")
                sw = psutil.swap_memory()
                if sw.total > 0:
                    lines.append(f"Підкачка:   {sw.total/1024**3:.1f} ГБ")
            gpu2 = "N/A"
            try:
                r3 = _run_hidden(["wmic","path","win32_VideoController","get","Name"],
                              capture_output=True, text=True, timeout=3)
                gl2 = [l.strip() for l in r3.stdout.splitlines() if l.strip() and l.strip() != "Name"]
                if gl2:
                    gpu2 = " | ".join(gl2)
            except: pass
            if gpu2 == "N/A":
                try:
                    ps_cmd2 = ["powershell", "-NoProfile", "-Command",
                               "(Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name) -join ' | '"]
                    rp2 = _run_hidden(ps_cmd2, capture_output=True, text=True, timeout=4)
                    gp2 = rp2.stdout.strip()
                    if gp2:
                        gpu2 = gp2
                except: pass
            lines.append(f"GPU:        {gpu2}")
            try:
                disk = psutil.disk_usage(CONFIG_DIR)
                lines.append(f"Диск:       {disk.free/1024**3:.1f} ГБ вільно / {disk.total/1024**3:.0f} ГБ")
            except: pass
            lines.append(f"ОС:         {platform.system()} {platform.release()} ({platform.machine()})")
            try: lines.append(f"Комп'ютер: {socket.gethostname()}")
            except: pass
            lines.append(f"Python:     {platform.python_version()}")
            try:
                jr2 = _run_hidden(["java","-version"], capture_output=True, text=True, timeout=3)
                jl2 = (jr2.stderr or jr2.stdout).splitlines()
                lines.append(f"Java:       {jl2[0] if jl2 else 'не знайдено'}")
            except: lines.append("Java:       не знайдено")
            specs_text2.setPlainText("\n".join(lines))
        except Exception as _e2:
            specs_text2.setPlainText(f"Помилка: {_e2}")
 
        def _toggle_specs2(checked):
            btn_specs2.setText(("▼" if checked else "▶") + "  Характеристики пристрою")
            specs_text2.setVisible(checked)
        btn_specs2.toggled.connect(_toggle_specs2)
        info_vbox.addWidget(btn_specs2)
        info_vbox.addWidget(specs_text2)
 
        lay_about.addWidget(info_box)
        lay_about.addStretch()
        self._settings_tabs.addTab(tab_about, "ℹ  Про програму")
 
    # ── MODS PAGE ──
    # ── ABOUT PAGE ──
    def init_about_page(self):
        layout = QVBoxLayout(self.about_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
 
        header = QWidget()
        header.setFixedHeight(160)
        header.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #1b5e20, stop:0.5 #2e7d32, stop:1 #388e3c);
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)
 
        logo_lbl = QLabel(LOGO_HTML)
        logo_lbl.setFont(QFont("Arial", 36, QFont.Bold))
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 36pt; background: transparent;")
        h_layout.addWidget(logo_lbl)
 
        tagline = QLabel("Твій шлях до Minecraft")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("color: #a5d6a7; font-size: 13px; background: transparent;")
        h_layout.addWidget(tagline)
 
        layout.addWidget(header)
 
        content = QWidget()
        content.setStyleSheet("background-color: #1e1e1e;")
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(50, 30, 50, 30)
        c_layout.setSpacing(20)
 
        def info_card(title, value, color="#4caf50"):
            """Use QLineEdit (readonly) to guarantee NO rich-text parsing, NO brackets."""
            card = QFrame()
            card.setStyleSheet(
                f"background: #252525; border-radius: 8px; border-left: 4px solid {color};"
                " border-right: none; border-top: none; border-bottom: none;"
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(0)
 
            # Value — readonly QLineEdit, no rich-text engine
            from PyQt5.QtWidgets import QLineEdit as _QLEi
            v = _QLEi(value)
            v.setReadOnly(True)
            v.setFrame(False)
            v.setFont(QFont("Segoe UI", 11, QFont.Bold))
            v.setStyleSheet(
                f"color: {color}; background: transparent; border: none;"
                " selection-background-color: transparent;"
            )
            v.setCursorPosition(0)
 
            # Title — also QLineEdit so rendering is identical
            t = _QLEi(title)
            t.setReadOnly(True)
            t.setFrame(False)
            t.setAlignment(Qt.AlignRight)
            t.setFont(QFont("Segoe UI", 10))
            t.setStyleSheet(
                "color: #555; background: transparent; border: none;"
                " selection-background-color: transparent;"
            )
 
            cl.addWidget(v, 1)
            cl.addWidget(t, 1)
            return card
 
        c_layout.addWidget(info_card("Версія лаунчера", "1.4 FP 1 (Fix Pack 1)", "#4caf50"))
        c_layout.addWidget(info_card("Розробник", "ALFA Studios", "#4da6ff"))
 
        # ── Collapsible specs button ──
        btn_specs = QPushButton("▶  Характеристики пристрою")
        btn_specs.setCheckable(True)
        btn_specs.setChecked(False)
        btn_specs.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 8px 12px;
                background: #252525; color: #888;
                border: 1px solid #383838; border-radius: 6px;
                font-size: 12px; font-weight: normal;
            }
            QPushButton:checked {
                background: #1e2a1e; color: #9ccc65;
                border: 1px solid #4caf50;
            }
            QPushButton:hover { background: #2e2e2e; }
        """)
 
        from PyQt5.QtWidgets import QTextEdit as _QTE
        specs_text = _QTE()
        specs_text.setReadOnly(True)
        specs_text.setVisible(False)
        specs_text.setMaximumHeight(220)
        specs_text.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a; color: #ccc;
                border: 1px solid #333; border-top: none;
                border-radius: 0 0 6px 6px;
                font-family: Consolas, monospace; font-size: 11px;
                padding: 8px;
            }
        """)
 
        # Build specs text
        try:
            import multiprocessing, socket
            lines = []
            cpu_name = platform.processor() or platform.machine() or "N/A"
            try:
                freq = psutil.cpu_freq()
                freq_s = f" @ {freq.max/1000:.1f} GHz" if freq else ""
            except: freq_s = ""
            lines.append(f"CPU:        {cpu_name}{freq_s}")
            lines.append(f"Ядра:       {multiprocessing.cpu_count()}")
            if psutil:
                vm = psutil.virtual_memory()
                lines.append(f"ОЗУ:        {vm.total/1024**3:.1f} ГБ  (зайнято {vm.percent:.0f}%)")
                sw = psutil.swap_memory()
                if sw.total > 0:
                    lines.append(f"Підкачка:   {sw.total/1024**3:.1f} ГБ")
            gpu = "N/A"
            try:
                r = _run_hidden(["wmic","path","win32_VideoController","get","Name"],
                             capture_output=True, text=True, timeout=3)
                gl = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip() != "Name"]
                if gl:
                    gpu = " | ".join(gl)
            except: pass
            if gpu == "N/A":
                try:
                    ps_cmd = ["powershell", "-NoProfile", "-Command",
                              "(Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name) -join ' | '"]
                    rp = _run_hidden(ps_cmd, capture_output=True, text=True, timeout=4)
                    gp = rp.stdout.strip()
                    if gp:
                        gpu = gp
                except: pass
            lines.append(f"GPU:        {gpu}")
            try:
                disk = psutil.disk_usage(CONFIG_DIR)
                lines.append(f"Диск:       {disk.free/1024**3:.1f} ГБ вільно / {disk.total/1024**3:.0f} ГБ")
            except: pass
            lines.append(f"ОС:         {platform.system()} {platform.release()} ({platform.machine()})")
            try: lines.append(f"Комп'ютер: {socket.gethostname()}")
            except: pass
            lines.append(f"Python:     {platform.python_version()}")
            try:
                jr = _run_hidden(["java","-version"], capture_output=True, text=True, timeout=3)
                jl = (jr.stderr or jr.stdout).splitlines()
                lines.append(f"Java:       {jl[0] if jl else 'не знайдено'}")
            except: lines.append("Java:       не знайдено")
            specs_text.setPlainText("\n".join(lines))
        except Exception as _e:
            specs_text.setPlainText(f"Помилка: {_e}")
 
        def _toggle_specs(checked):
            btn_specs.setText(("▼" if checked else "▶") + "  Характеристики пристрою")
            specs_text.setVisible(checked)
        btn_specs.toggled.connect(_toggle_specs)
 
        c_layout.addWidget(btn_specs)
        c_layout.addWidget(specs_text)
 
        c_layout.addStretch()
 
        btns_row = QHBoxLayout()
        btn_site = QPushButton("🌐 Сайт проекту")
        btn_site.setToolTip("Відкрити сайт проекту")
        btn_site.clicked.connect(lambda: self._open_url("https://devalfastudios.github.io/G9-Launcher/"))
        btn_check_upd = QPushButton("🔄 Перевірити оновлення")
        btn_check_upd.setStyleSheet("background: #1565c0; color: white; padding: 6px 14px; border-radius: 6px; font-weight: bold;")
        btn_check_upd.clicked.connect(lambda: self.check_for_update_now(silent=False))
        btn_back = QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btns_row.addWidget(btn_back)
        btns_row.addStretch()
        btns_row.addWidget(btn_check_upd)
        btns_row.addWidget(btn_site)
        c_layout.addLayout(btns_row)
 
        layout.addWidget(content)
 
    # ── ACCOUNTS PAGE ──
    def init_accounts_page(self):
        layout = QVBoxLayout(self.accounts_page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)
 
        title = QLabel("Менеджер Акаунтів")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #4caf50; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
 
        self.skin_viewer = SkinViewer()
        self.skin_viewer_nick = QLabel(self.nick_dialog.current_nick)
        self.skin_viewer_nick.setAlignment(Qt.AlignCenter)
        self.skin_viewer_nick.setStyleSheet("color: #4caf50; font-weight: bold; background: transparent;")
 
        skin_row = QHBoxLayout()
        skin_col = QVBoxLayout()
        skin_col.addWidget(self.skin_viewer, 0, Qt.AlignCenter)
        skin_col.addWidget(self.skin_viewer_nick)
        skin_row.addLayout(skin_col)
 
        self.accounts_list = QListWidget()
        self.accounts_list.setStyleSheet(
            "background-color: #2b2b2b; color: white; border-radius: 8px; font-size: 14px; border: 1px solid #444;")
        if os.path.exists(NICKS_FILE):
            try:
                with open(NICKS_FILE, "r", encoding="utf-8") as f:
                    for n in json.load(f):
                        self.accounts_list.addItem(n)
            except:
                pass
 
        self.accounts_list.itemClicked.connect(
            lambda item: self.skin_viewer.load_for_nick(item.text()))
 
        skin_row.addWidget(self.accounts_list)
        layout.addLayout(skin_row)
 
        self.new_nick_input = QLineEdit()
        self.new_nick_input.setPlaceholderText("Введіть новий нік...")
        self.new_nick_input.setStyleSheet(
            "background: #333; padding: 10px; color: white; border-radius: 5px; border: 1px solid #555;")
        layout.addWidget(self.new_nick_input)
 
        btns = QHBoxLayout()
        btn_add = QPushButton("➕ Додати")
        btn_add.clicked.connect(self.add_account_logic)
        btn_del = QPushButton("🗑 Видалити")
        btn_del.setStyleSheet("background-color: #c62828;")
        btn_del.clicked.connect(self.delete_account_logic)
        btn_sel = QPushButton("✔ Вибрати")
        btn_sel.clicked.connect(self.apply_account_logic)
        for b in [btn_add, btn_del, btn_sel]:
            b.setMinimumHeight(38)
            btns.addWidget(b)
        layout.addLayout(btns)
 
        btn_back = QPushButton("← Назад до головної")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(btn_back)
 
    # ── ACCOUNTS LOGIC ──
    def add_account_logic(self):
        nick = self.new_nick_input.text().strip()
        if nick:
            if QMessageBox.question(self, "Підтвердження", f"Додати нік '{nick}'?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.accounts_list.addItem(nick)
                self.new_nick_input.clear()
                self.save_accounts_to_file()
        else:
            QMessageBox.warning(self, "Помилка", "Нік порожній!")
 
    def delete_account_logic(self):
        item = self.accounts_list.currentItem()
        if item:
            if QMessageBox.question(self, "Видалення", f"Видалити '{item.text()}'?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.accounts_list.takeItem(self.accounts_list.row(item))
                self.save_accounts_to_file()
        else:
            QMessageBox.warning(self, "Помилка", "Виберіть нік у списку!")
 
    def apply_account_logic(self):
        item = self.accounts_list.currentItem()
        if item:
            nick = item.text()
            self.nick_dialog.current_nick = nick
            self.btn_nick.setText(f"Нік: {nick}")
            self.skin_viewer_nick.setText(nick)
            self.save_settings()
            self.stacked_widget.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Помилка", "Виберіть нік зі списку!")
 
    def save_accounts_to_file(self):
        nicks = [self.accounts_list.item(i).text() for i in range(self.accounts_list.count())]
        try:
            with open(NICKS_FILE, "w", encoding="utf-8") as f:
                json.dump(nicks, f, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження ніків: {e}")
 
    # ── PLAY ──
    def toggle_play(self):
        if not self.is_playing:
            self.start_game()
        else:
            self.stop_game()
 
    def start_game(self):
        if not HAS_LAUNCHER_LIB:
            QMessageBox.critical(self, "Помилка", "minecraft_launcher_lib не встановлено!\npip install minecraft-launcher-lib")
            return
 
        selected = self._current_version_text()
        mc_ver, loader = get_mc_ver_and_loader(selected)
 
        self.btn_play.setText("Завантаження...")
        self.btn_play.setEnabled(False)
 
        self.launch_progress.show()
        self.launch_progress.setRange(0, 100)
        self.launch_progress.setValue(0)
        self._progress_anim = QPropertyAnimation(self.launch_progress, b"value")
        self._progress_anim.setDuration(15000)
        self._progress_anim.setStartValue(0)
        self._progress_anim.setEndValue(90)
        self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._progress_anim.start()
 
        self.discord.update_playing(selected, self.nick_dialog.current_nick)
 
        def run():
            try:
                # Install the version; allow snapshots/pre-releases
                try:
                    minecraft_launcher_lib.install.install_minecraft_version(
                        mc_ver, CONFIG_DIR, allow_snapshots=True, allow_experimental=True)
                except TypeError:
                    # Older minecraft_launcher_lib without those kwargs
                    minecraft_launcher_lib.install.install_minecraft_version(mc_ver, CONFIG_DIR)
 
                if loader == "forge":
                    try:
                        fv = minecraft_launcher_lib.forge.find_forge_version(mc_ver)
                        if fv:
                            minecraft_launcher_lib.forge.install_forge_version(fv, CONFIG_DIR)
                    except:
                        pass
                elif loader == "fabric":
                    try:
                        minecraft_launcher_lib.fabric.install_fabric(mc_ver, CONFIG_DIR)
                    except:
                        pass
                elif loader in ("neoforge", "quilt"):
                    try:
                        ml = minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
                        ml.install(mc_ver, CONFIG_DIR)
                    except:
                        pass
 
                launch_id = mc_ver
                if loader:
                    installed = minecraft_launcher_lib.utils.get_installed_versions(CONFIG_DIR)
                    for v in installed:
                        vid = v.get("id", "")
                        if loader in vid.lower() and mc_ver in vid:
                            launch_id = vid
                            break
 
                nick = self.nick_dialog.current_nick
                player_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, nick))
                mc_game_dir = os.path.join(CONFIG_DIR, "minecraft")
                os.makedirs(mc_game_dir, exist_ok=True)
                extra_jvm = []
                try:
                    raw = self.jvm_args_input.text().strip()
                    if raw:
                        extra_jvm = raw.split()
                except Exception:
                    pass

                # Визначаємо java для старих версій (fallback).
                # ВАЖЛИВО: НЕ встановлюємо executablePath — тоді minecraft_launcher_lib
                # сам підбере правильний JRE з version.json (Java 25 для 26.x тощо).
                # defaultExecutablePath використовується ТІЛЬКИ якщо у version.json немає runtime.
                custom_java = ""
                try:
                    lbl = getattr(self, "java_path_lbl", None)
                    if lbl:
                        p = lbl.text().strip()
                        if p and os.path.isfile(p):
                            custom_java = p
                except Exception:
                    pass

                fallback_java = custom_java or shutil.which("java") or "java"

                options = {
                    "username": nick,
                    "uuid": player_uuid,
                    "token": "0",
                    "defaultExecutablePath": fallback_java,
                    "gameDirectory": mc_game_dir,
                    "jvmArguments": [
                        f"-Xmx{self.ram_slider.value()}G",
                        "-Xms512M",
                        "-XX:+UseG1GC",
                    ] + extra_jvm,
                    "launcherName": "G9Launcher",
                    "launcherVersion": "1.4 FP 1",
                }
                cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_id, CONFIG_DIR, options)
                # Фільтруємо застарілі JVM аргументи несумісні з Java 21+/25
                _bad_args = {
                    "--sun-misc-unsafe-memory-access=allow",
                    "-XX:+UnlockExperimentalVMOptions",
                }
                cmd = [a for a in cmd if a not in _bad_args]
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                self.minecraft_process = subprocess.Popen(cmd, startupinfo=si, cwd=CONFIG_DIR)
                QTimer.singleShot(0, self.finish_start)
                QTimer.singleShot(500, self.refresh_version_combo)
                QTimer.singleShot(0, self.save_settings)
            except Exception as e:
                err = f"Не вдалось запустити Minecraft:\n\n{e}\n\nВерсія: {selected}"
                QTimer.singleShot(0, lambda t=err: QMessageBox.critical(self, "Помилка запуску", t))
                QTimer.singleShot(0, self.stop_game)
 
        Thread(target=run, daemon=True).start()
 
    def finish_start(self):
        self.is_playing = True
        self.btn_play.setEnabled(True)
        self.btn_play.setText("■ Зупинити")
        self.btn_play.setObjectName("StopButton")
        self.setStyleSheet(self.styleSheet())
        if hasattr(self, "_progress_anim"):
            self._progress_anim.stop()
        done = QPropertyAnimation(self.launch_progress, b"value")
        done.setDuration(400)
        done.setStartValue(self.launch_progress.value())
        done.setEndValue(100)
        done.setEasingCurve(QEasingCurve.OutCubic)
        done.finished.connect(lambda: QTimer.singleShot(600, self.launch_progress.hide))
        done.start()
        self._progress_done = done
        if hasattr(self, 'chk_hide_on_launch') and self.chk_hide_on_launch.isChecked():
            QTimer.singleShot(1200, self.hide)
            self._start_game_watcher()
 
    def _start_game_watcher(self):
        def watch():
            try:
                if hasattr(self, 'minecraft_process'):
                    self.minecraft_process.wait()
            except Exception:
                pass
            QTimer.singleShot(0, self._on_game_closed)
        Thread(target=watch, daemon=True).start()
 
    def _on_game_closed(self):
        self.stop_game()
        if not self.isVisible():
            self.show()
            self.setWindowOpacity(0.0)
            fade = QPropertyAnimation(self, b'windowOpacity')
            fade.setDuration(400)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)
            fade.setEasingCurve(QEasingCurve.OutCubic)
            fade.start()
            self._restore_fade = fade
 
    def stop_game(self):
        if hasattr(self, "minecraft_process") and self.minecraft_process.poll() is None:
            self.minecraft_process.terminate()
        self.is_playing = False
        self.btn_play.setEnabled(True)
        self.btn_play.setText("▶  Грати")
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.setStyleSheet("")
        if hasattr(self, "_progress_anim"):
            self._progress_anim.stop()
        self.launch_progress.hide()
        self.launch_progress.setValue(0)
        self.discord.update("В меню", "G9 Launcher")
 
    # ── MINIMIZE / CLOSE ANIMATIONS ──
    def _animate_minimize(self):
        anim_fade = QPropertyAnimation(self, b"windowOpacity")
        anim_fade.setDuration(180)
        anim_fade.setStartValue(1.0)
        anim_fade.setEndValue(0.0)
        anim_fade.setEasingCurve(QEasingCurve.InQuad)
 
        anim_pos = QPropertyAnimation(self, b"pos")
        anim_pos.setDuration(180)
        anim_pos.setStartValue(self.pos())
        anim_pos.setEndValue(QPoint(self.x(), self.y() + 20))
        anim_pos.setEasingCurve(QEasingCurve.InQuad)
 
        group = QParallelAnimationGroup(self)
        group.addAnimation(anim_fade)
        group.addAnimation(anim_pos)
 
        def _finish():
            self.showMinimized()
            self.setWindowOpacity(1.0)
            self.move(self.x(), self.y() - 20)
 
        group.finished.connect(_finish)
        group.start()
        self._minimize_anim = group
 
    def _animate_close(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self.close)
        anim.start()
        self._close_anim = anim
 
    # ── BG ──
    def _apply_bg_type(self):
        """Apply background based on currently selected type."""
        bg_type = getattr(self, "bg_type_combo", None)
        if bg_type is None:
            return
        t = bg_type.currentText()
        # Always clear home_page border-image override first
        self.home_page.setStyleSheet("")
        if t == "Фон Колір":
            color = getattr(self, "_color_bg", "#2b2b2b")
            self._bg_label.setPixmap(QPixmap())
            self._bg_label.setStyleSheet(f"background: {color};")
        elif t == "Ваш Фон":
            path = getattr(self, "_bg_path", "")
            if path and os.path.exists(path):
                pix = QPixmap(path)
                if not pix.isNull() and hasattr(self, "_bg_label"):
                    self._bg_label.setPixmap(
                        pix.scaled(self._bg_label.width() or 800,
                                   self._bg_label.height() or 400,
                                   Qt.KeepAspectRatioByExpanding,
                                   Qt.SmoothTransformation))
            else:
                self._bg_label.setPixmap(QPixmap())
                self._bg_label.setStyleSheet("background: #1a1a1a;")

    def change_background(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Вибрати фон", "", "Images (*.png *.jpg *.jpeg)")
        if fname:
            clean = fname.replace(os.sep, "/")
            self._bg_path = clean
            if hasattr(self, "_bg_file_label"):
                self._bg_file_label.setText(os.path.basename(clean))
            self._apply_bg_type()
            self.save_settings()
 
    def reset_background(self):
        self._bg_path = ""
        if hasattr(self, "_bg_file_label"):
            self._bg_file_label.setText("Не вибрано")
        self.home_page.setStyleSheet("")
        if hasattr(self, "_bg_label"):
            self._bg_label.setPixmap(QPixmap())
            color = getattr(self, "_color_bg", "#2b2b2b")
            self._bg_label.setStyleSheet(f"background: {color};")
        self.save_settings()
 
    # ── JAVA PATH ──
    def change_java_path(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Вибрати Java", "", "Java executable (java.exe java *)")
        if fname and hasattr(self, "java_path_lbl"):
            self.java_path_lbl.setText(fname)

    # ── OPEN URL ──
    def _open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            try:
                os.startfile(url)
            except Exception:
                pass

    # ── AUTOSTART ──
    _AUTOSTART_NAME = "G9Launcher"

    def _get_autostart_enabled(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, self._AUTOSTART_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def _set_autostart(self, enabled: bool):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if enabled:
                exe = os.path.abspath(sys.argv[0])
                # якщо запускається як .py — через python
                if exe.endswith(".py"):
                    value = f'"{sys.executable}" "{exe}"'
                else:
                    value = f'"{exe}"'
                winreg.SetValueEx(key, self._AUTOSTART_NAME, 0, winreg.REG_SZ, value)
            else:
                try:
                    winreg.DeleteValue(key, self._AUTOSTART_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"autostart error: {e}")
            return False

    # ── UPDATE CHECK / INSTALL ──
    def check_for_update_now(self, silent=False):
        """Перевіряє оновлення і показує результат. silent=True — тільки якщо є нове."""
        def _worker():
            info = _fetch_latest_release_info()
            if not info:
                if not silent:
                    QTimer.singleShot(0, lambda: QMessageBox.information(
                        self, "Оновлення", "Не вдалося перевірити оновлення.\nПеревірте підключення до інтернету."))
                return
            tag = info.get("tag_name", "")
            url = info.get("html_url", "")
            assets = info.get("assets", [])
            body = info.get("body", "")
            # Знаходимо .py або .exe у релізі
            dl_url = ""
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".py") or name.endswith(".exe"):
                    dl_url = asset.get("browser_download_url", "")
                    break
            if _is_newer_version(tag, _LAUNCHER_VERSION):
                def _show():
                    notes = body[:400] + ("…" if len(body) > 400 else "") if body else ""
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Доступне оновлення!")
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(
                        f"<b>Доступна нова версія G9 Launcher: {tag}</b><br><br>"
                        f"{notes.replace(chr(10), '<br>') if notes else ''}"
                        f"<br><br>Після завантаження <b>лаунчер перезапуститься</b>."
                    )
                    btn_install = msg.addButton("⬇  Встановити оновлення", QMessageBox.AcceptRole)
                    btn_web     = msg.addButton("🌐 Відкрити сторінку", QMessageBox.ActionRole)
                    msg.addButton("Пізніше", QMessageBox.RejectRole)
                    msg.exec_()
                    clicked = msg.clickedButton()
                    if clicked == btn_install and dl_url:
                        self._download_and_apply_update(dl_url, tag)
                    elif clicked == btn_web:
                        self._open_url(url)
                QTimer.singleShot(0, _show)
            else:
                if not silent:
                    QTimer.singleShot(0, lambda: QMessageBox.information(
                        self, "Оновлення", f"У вас вже встановлена остання версія ({_LAUNCHER_VERSION})."))
        Thread(target=_worker, daemon=True).start()

    def _download_and_apply_update(self, dl_url, tag):
        """Завантажує файл оновлення і перезапускає лаунчер."""
        import tempfile
        def _worker():
            try:
                ext = ".exe" if dl_url.lower().endswith(".exe") else ".py"
                current = os.path.abspath(sys.argv[0])
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
                os.close(tmp_fd)
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    self, "Завантаження", f"Завантаження оновлення {tag}...\nЛаунчер повідомить коли готово."))
                req = urllib.request.Request(dl_url, headers={"User-Agent": f"G9Launcher/{_LAUNCHER_VERSION}"})
                with urllib.request.urlopen(req, timeout=60) as r, open(tmp_path, "wb") as f:
                    f.write(r.read())
                # Замінюємо поточний файл і перезапускаємо
                backup = current + ".bak"
                try:
                    if os.path.exists(backup):
                        os.remove(backup)
                    os.rename(current, backup)
                except Exception:
                    pass
                import shutil as _sh
                _sh.copy2(tmp_path, current)
                os.remove(tmp_path)
                def _restart():
                    reply = QMessageBox.question(
                        self, "Оновлення завантажено",
                        f"Оновлення {tag} завантажено!\nЛаунчер зараз перезапуститься.",
                        QMessageBox.Ok)
                    if ext == ".exe":
                        subprocess.Popen([current])
                    else:
                        subprocess.Popen([sys.executable, current])
                    self.close()
                QTimer.singleShot(0, _restart)
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(
                    self, "Помилка оновлення", f"Не вдалося завантажити оновлення:\n{e}"))
        Thread(target=_worker, daemon=True).start()
 
    # ── SCREENSHOTS ──
    def open_screenshots(self):
        path = os.path.join(CONFIG_DIR, "screenshots")
        os.makedirs(path, exist_ok=True)
        try:
            os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося відкрити: {e}")
 
    # ── PALETTE ──
    def _apply_palette(self):
        # Guard against recursive calls (e.g. app.setFont triggers widget signals)
        if getattr(self, "_applying_palette", False):
            return
        self._applying_palette = True
        try:
            acc  = getattr(self, "_color_accent",  "#4caf50")
            side = getattr(self, "_color_sidebar", "#212121")
            bg   = getattr(self, "_color_bg",      "#2b2b2b")
            txt  = getattr(self, "_color_text",    "#ffffff")
            font_family = getattr(self, "_ui_font_family", "Segoe UI")
            font_size   = getattr(self, "_ui_font_size",   10)
 
            # Update app-level font (blocked from re-triggering via guard)
            app = QApplication.instance()
            f = app.font()
            f.setFamily(font_family)
            f.setPointSize(font_size)
            app.setFont(f)
 
            def darken(hex_c, factor=0.75):
                c = QColor(hex_c)
                return QColor(int(c.red()*factor), int(c.green()*factor), int(c.blue()*factor)).name()
            def lighten(hex_c, factor=1.2):
                c = QColor(hex_c)
                return QColor(min(255,int(c.red()*factor)), min(255,int(c.green()*factor)), min(255,int(c.blue()*factor))).name()
 
            acc_dark  = darken(acc)
            acc_light = lighten(acc)
            input_bg  = lighten(bg, 1.15)
 
            theme = f"""
QScrollBar:vertical {{ border: none; background: {bg}; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {acc}; min-height: 20px; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QWidget {{ background-color: {bg}; color: {txt}; font-family: '{font_family}', Arial, sans-serif; font-size: {font_size}pt; }}
QPushButton {{ background-color: {acc_dark}; color: {txt}; border: 2px solid {darken(acc_dark)}; padding: 6px; border-radius: 4px; font-weight: bold; }}
QPushButton:hover {{ background-color: {acc}; border: 2px solid {acc_dark}; }}
QPushButton:pressed {{ background-color: {darken(acc_dark)}; }}
QComboBox, QLineEdit, QListWidget {{ background-color: {input_bg}; border: 1px solid #555; color: {txt}; padding: 4px; }}
QProgressBar {{ border: 1px solid #555; background-color: {input_bg}; height: 10px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background-color: {acc}; }}
#PlayButton {{ font-size: {font_size + 6}pt; padding: 10px; background-color: {acc}; border: 2px solid {acc_dark}; }}
#PlayButton:hover {{ background-color: {acc_light}; }}
#StopButton {{ background-color: #e53935; border: 2px solid #c62828; }}
#StopButton:hover {{ background-color: #ef5350; }}
"""
            self.setStyleSheet(theme)
            # Sidebar panel
            try:
                side_panel = self.centralWidget().findChildren(QWidget)[0]
                side_panel.setStyleSheet(f"background-color: {side};")
            except:
                pass
            # Title bar
            try:
                tb_c = getattr(self, "_color_titlebar", side)
                self.title_bar.setStyleSheet(f"background-color: {tb_c}; border-bottom: 1px solid {acc};")
            except:
                pass
            # Bottom panel
            try:
                self.bottom_bar.setStyleSheet(f"background-color: {darken(bg)}; border-top: 2px solid {acc};")
            except:
                pass
            # Logo accent
            try:
                self.logo_label.setStyleSheet(f"font-size: 20pt; background: transparent; color: {acc};")
            except:
                pass
            # Update bg label color if bg type is "Фон Колір"
            try:
                bg_type_w = getattr(self, "bg_type_combo", None)
                if bg_type_w and bg_type_w.currentText() == "Фон Колір":
                    self._bg_label.setStyleSheet(f"background: {bg};")
            except:
                pass
            for attr, dflt in [("_color_accent","#4caf50"),("_color_sidebar","#212121"),("_color_bg","#2b2b2b"),("_color_text","#ffffff")]:
                preview = getattr(self, attr + "_preview", None)
                if preview:
                    c2 = getattr(self, attr, dflt)
                    preview.setStyleSheet(f"background: {c2}; border-radius: 4px; border: 1px solid #555;")
        finally:
            self._applying_palette = False
 
    # ── NEWS ──
    def _open_news_reader(self, nd):
        d = QDialog(self); d.setWindowTitle(nd.get("title","Новина")); d.setMinimumSize(580,400)
        d.setStyleSheet("QDialog{background:#1a1a1a;}QLabel{background:transparent;color:#e8e8e8;}"
                        "QPushButton{background:#2e7d32;color:white;border:none;border-radius:6px;"
                        "padding:8px 20px;font-weight:bold;}QPushButton:hover{background:#4caf50;}")
        vl=QVBoxLayout(d); vl.setContentsMargins(24,20,24,20); vl.setSpacing(12)
        mr=QHBoxLayout(); cat=nd.get("category","")
        if cat:
            cl2=QLabel(cat); cl2.setStyleSheet("background:#1a2e1a;color:#4caf50;font-size:11px;"
                "font-weight:bold;padding:3px 10px;border-radius:4px;"); mr.addWidget(cl2)
        mr.addStretch(); dl2=QLabel(nd.get("date","")); dl2.setStyleSheet("color:#666;font-size:12px;")
        mr.addWidget(dl2); vl.addLayout(mr)
        tl=QLabel(nd.get("title","")); tl.setWordWrap(True)
        tl.setStyleSheet("font-size:20px;font-weight:900;color:#fff;"); vl.addWidget(tl)
        sp=QFrame(); sp.setFrameShape(QFrame.HLine); sp.setStyleSheet("background:#333;border:none;max-height:1px;")
        vl.addWidget(sp)
        from PyQt5.QtWidgets import QScrollArea
        sc=QScrollArea(); sc.setWidgetResizable(True)
        sc.setStyleSheet("QScrollArea{border:none;background:transparent;}"
                         "QScrollBar:vertical{background:#111;width:6px;}QScrollBar::handle:vertical{background:#444;}")
        cw=QWidget(); cw.setStyleSheet("background:transparent;"); cl3=QVBoxLayout(cw); cl3.setContentsMargins(0,8,12,8)
        bl=QLabel(nd.get("body",nd.get("summary",""))); bl.setWordWrap(True)
        bl.setStyleSheet("font-size:14px;color:#ccc;"); bl.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        cl3.addWidget(bl); cl3.addStretch(); sc.setWidget(cw); vl.addWidget(sc,1)
        bcl=QPushButton("✕  Закрити"); bcl.clicked.connect(d.accept)
        vl.addWidget(bcl,0,Qt.AlignRight); d.exec_()

    def _load_news_async(self):
        result = fetch_news()
        self._news_ready.emit(result)

    def _render_news(self, payload):
        news, err = payload if isinstance(payload, tuple) else (payload, None)
        if not getattr(self, "_show_news", True):
            return
        while self.news_list_layout.count():
            item = self.news_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if err == "no_internet":
            lbl = QLabel("🌐 Новини потребують\nпідключення до інтернету")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background:transparent;color:#666;font-size:12px;padding:20px;")
            self.news_list_layout.addWidget(lbl)
            self.news_list_layout.addStretch()
            return
        for n in news[:6]:
            card = QWidget()
            card.setStyleSheet(
                "QWidget { background:#1e1e1e; border-radius:6px; border:1px solid #2a2a2a; }"
                "QWidget:hover { background:#252525; border:1px solid #2e7d32; }"
            )
            card.setCursor(Qt.PointingHandCursor)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(4)

            title_lbl = QLabel(n.get("title", ""))
            title_lbl.setWordWrap(True)
            title_lbl.setStyleSheet(
                "background:transparent; border:none; color:#e8e8e8; "
                "font-size:13px; font-weight:bold; line-height:1.3;"
            )
            card_layout.addWidget(title_lbl)

            summary = n.get("summary", "")
            if summary:
                sum_lbl = QLabel(summary[:80] + ("..." if len(summary) > 80 else ""))
                sum_lbl.setWordWrap(True)
                sum_lbl.setStyleSheet(
                    "background:transparent; border:none; color:#888; font-size:12px;"
                )
                card_layout.addWidget(sum_lbl)

            date = n.get("date", "")
            if date:
                date_lbl = QLabel(date)
                date_lbl.setStyleSheet(
                    "background:transparent; border:none; color:#4caf50; font-size:11px;"
                )
                card_layout.addWidget(date_lbl)

            card.mousePressEvent = lambda e, nd=n: self._open_news_reader(nd)
            self.news_list_layout.addWidget(card)

        self.news_list_layout.addStretch()

    # ── SIDEBAR ORDER ──
    def _apply_sidebar_order(self):
        """Re-adds sidebar buttons in the user-defined order."""
        order = getattr(self, "_sidebar_button_order",
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти", "🌐 Сайт"])
        btn_map = {
            "⚙ Налаштування": self.btn_settings,
            "👤 Аккаунти":     self.btn_accounts,
            "📁 Папка гри":    self.btn_folder,
            "🖼 Скріншоти":    self.btn_screens,
        }
        # Find the site button by object name
        btn_site = getattr(self, "_btn_site", None)
        if btn_site:
            btn_map["🌐 Сайт"] = btn_site

        layout = getattr(self, "_side_layout", None)
        if layout is None:
            return
        # Remove all nav buttons (leave logo + stretch)
        for key, b in btn_map.items():
            layout.removeWidget(b)
            b.setParent(None)

        # Re-insert in new order (after logo spacer = index 2)
        insert_pos = 2
        for name in order:
            b = btn_map.get(name)
            if b is not None:
                layout.insertWidget(insert_pos, b)
                insert_pos += 1

    # ── UI STYLE ──
    def _apply_ui_style(self):
        style = getattr(self, "_ui_style", "G9 UI")

        if style == "MetroUI":
            # ── Full Metro: tile sidebar + flat UI ──
            # Style the main window and widgets
            acc   = getattr(self, "_color_accent",  "#4caf50")
            side  = getattr(self, "_color_sidebar", "#212121")
            bg    = getattr(self, "_color_bg",      "#2b2b2b")
            # darken accent for pressed states
            def _darken(h, pct=20):
                h=h.lstrip('#'); r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
                r,g,b=max(0,r-pct),max(0,g-pct),max(0,b-pct)
                return f'#{r:02x}{g:02x}{b:02x}'
            acc_dark = _darken(acc, 30)
            acc_dim  = acc + "55"
            bg_dark  = _darken(bg, 15)
            metro_css = f"""
                QMainWindow {{ background: {bg}; }}
                QWidget {{ background: {bg}; color: #ffffff; border-radius: 0px; }}
                QGroupBox {{
                    background: {bg_dark};
                    border: none;
                    border-left: 3px solid {acc};
                    border-radius: 0px;
                    font-weight: bold;
                    color: {acc};
                    margin-top: 8px;
                    padding-top: 4px;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; left: 8px; color: {acc}; }}
                QPushButton {{
                    background: {acc};
                    color: #ffffff;
                    border: none;
                    border-radius: 0px;
                    font-weight: bold;
                    padding: 8px 16px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: {_darken(acc, -15)}; }}
                QPushButton:pressed {{ background: {acc_dark}; }}
                QPushButton#PlayButton {{
                    background: {acc};
                    font-size: 14px;
                    font-weight: bold;
                    border: 2px solid {_darken(acc, -10)};
                }}
                QPushButton#PlayButton:hover {{ background: {_darken(acc, -20)}; }}
                QPushButton#TitleBarBtn {{
                    background: transparent; border: none; border-radius: 4px;
                    color: #aaa; font-size: 18px; padding: 0;
                }}
                QPushButton#TitleBarBtn:hover {{ background: {acc_dim}; color: white; }}
                QPushButton#TitleBarClose {{
                    background: transparent; border: none; border-radius: 4px;
                    color: #aaa; font-size: 18px; padding: 0;
                }}
                QPushButton#TitleBarClose:hover {{ background: #c0392b; color: white; }}
                QComboBox {{
                    background: {bg_dark};
                    color: white;
                    border: 1px solid {acc};
                    border-radius: 0px;
                    padding: 4px;
                }}
                QComboBox::drop-down {{ border: none; background: {acc}; width: 24px; }}
                QScrollBar:vertical {{ background: {bg_dark}; width: 6px; }}
                QScrollBar::handle:vertical {{ background: {acc}; }}
                QLabel {{ background: transparent; color: #e8e8e8; }}
                QLineEdit {{ background: {bg_dark}; border: 1px solid {acc}; border-radius: 0px; color: white; padding: 4px; }}
                QSlider::groove:horizontal {{ background: {bg_dark}; height: 4px; }}
                QSlider::handle:horizontal {{ background: {acc}; width: 16px; height: 16px; margin: -6px 0; border-radius: 0px; }}
                QSlider::sub-page:horizontal {{ background: {acc}; }}
                QTabWidget::pane {{ border: 1px solid {acc}; background: {bg}; }}
                QTabBar::tab {{ background: {bg_dark}; color: #aaa; padding: 8px 16px; border: none; }}
                QTabBar::tab:selected {{ background: {acc}; color: white; }}
                QProgressBar {{ background: {bg_dark}; border: none; }}
                QProgressBar::chunk {{ background: {acc}; }}
            """
            self.setStyleSheet(metro_css)

            # Replace sidebar buttons with Metro tiles
            self._apply_metro_tiles()

        else:
            # G9 UI — reset
            self._restore_normal_sidebar()
            self._apply_palette()

    def _apply_metro_tiles(self):
        """Replace sidebar buttons with Metro-style colored tiles."""
        layout = getattr(self, "_side_layout", None)
        if layout is None:
            return

        # Tile config: respect saved order
        tile_data = {
            "⚙ Налаштування": ("⚙", "Налаштування", "#0078d7", lambda: self.switch_page(1)),
            "👤 Аккаунти":     ("👤", "Аккаунти",     "#e91e63", lambda: self.switch_page(3)),
            "📁 Папка гри":    ("📁", "Папка гри",    "#ff9800", lambda: os.startfile(CONFIG_DIR) if os.name == "nt" else None),
            "🖼 Скріншоти":    ("🖼", "Скріншоти",    "#9c27b0", self.open_screenshots),
            "🌐 Сайт":         ("🌐", "Сайт",         "#009688", lambda: None),
        }
        order = getattr(self, "_sidebar_button_order",
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти", "🌐 Сайт"])
        tiles_config = [tile_data[k] for k in order if k in tile_data]

        btn_map = {
            "Налаштування": self.btn_settings,
            "Аккаунти":     self.btn_accounts,
            "Папка гри":    self.btn_folder,
            "Скріншоти":    self.btn_screens,
            "Сайт":         getattr(self, "_btn_site", None),
        }

        # Hide original buttons
        for b in btn_map.values():
            if b: b.hide()

        # Remove existing metro widget if any
        if hasattr(self, "_metro_tiles_widget") and self._metro_tiles_widget:
            layout.removeWidget(self._metro_tiles_widget)
            self._metro_tiles_widget.deleteLater()
            self._metro_tiles_widget = None

        metro_widget = QWidget()
        metro_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(metro_widget)
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        for idx, (icon, label, color, action) in enumerate(tiles_config):
            tile = QPushButton()
            tile.setFixedSize(96, 68)
            tile.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 0px;
                    font-weight: bold;
                    text-align: left;
                    padding: 6px 8px;
                }}
                QPushButton:hover {{ background: {color}cc; }}
                QPushButton:pressed {{ background: {color}99; }}
            """)
            # Two-line label: icon big on top, text below
            tile_inner = QVBoxLayout(tile)
            tile_inner.setContentsMargins(6, 4, 6, 4)
            tile_inner.setSpacing(2)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"background:transparent; color:white; font-size:20px; border:none;")
            icon_lbl.setAlignment(Qt.AlignLeft)
            text_lbl = QLabel(label)
            text_lbl.setStyleSheet(f"background:transparent; color:white; font-size:10px; font-weight:bold; border:none;")
            tile_inner.addWidget(icon_lbl)
            tile_inner.addWidget(text_lbl)
            tile.clicked.connect(action)
            row, col = divmod(idx, 2)
            grid.addWidget(tile, row, col)

        self._metro_tiles_widget = metro_widget
        # Insert after logo (index 2)
        layout.insertWidget(2, metro_widget)

    def _restore_normal_sidebar(self):
        """Restore normal sidebar buttons (undo metro tiles)."""
        # Remove metro tiles widget if present
        if hasattr(self, "_metro_tiles_widget") and self._metro_tiles_widget:
            layout = getattr(self, "_side_layout", None)
            if layout:
                layout.removeWidget(self._metro_tiles_widget)
            self._metro_tiles_widget.deleteLater()
            self._metro_tiles_widget = None

        # Show original buttons again
        for b in [self.btn_settings, self.btn_accounts, self.btn_folder,
                  self.btn_screens, getattr(self, "_btn_site", None)]:
            if b: b.show()

    # ── BACKGROUND IMAGE LOADER ──
    def _load_bg_from_url(self, url):
        """Download image from URL and set as background label pixmap."""
        def _fetch():
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "G9Launcher/1.4"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = r.read()
                QTimer.singleShot(0, lambda: self._set_bg_pixmap(data))
            except Exception:
                pass  # keep dark bg if load fails
        from threading import Thread
        Thread(target=_fetch, daemon=True).start()

    def _set_bg_pixmap(self, data):
        from PyQt5.QtGui import QPixmap
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull() and hasattr(self, '_bg_label'):
            self._bg_label.setPixmap(pix)


    # ── RESET ALL ──
    def _confirm_reset_all(self):
        reply = QMessageBox.question(
            self, "Скидання налаштувань",
            "Ви впевнені, що хочете скинути ВСІ налаштування до стандартних?\n"
            "Кольори, шрифт, розмір вікна, фон — все буде скинуто.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._reset_all_settings()

    def _reset_all_settings(self):
        """Скидає всі налаштування до стандартних."""
        # Кольори
        self._color_accent   = "#4caf50"
        self._color_sidebar  = "#212121"
        self._color_bg       = "#2b2b2b"
        self._color_text     = "#ffffff"
        self._color_titlebar = "#212121"

        # Шрифт
        self._ui_font_family = "Segoe UI"
        self._ui_font_size   = 10
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.blockSignals(True)
            self.font_size_slider.setValue(10)
            self.font_size_slider.blockSignals(False)
            if hasattr(self, "font_size_lbl"):
                self.font_size_lbl.setText("10 pt")
        if hasattr(self, "font_combo"):
            self.font_combo.blockSignals(True)
            idx = self.font_combo.findText("Segoe UI")
            if idx >= 0: self.font_combo.setCurrentIndex(idx)
            self.font_combo.blockSignals(False)

        # Фон
        self._bg_path = ""
        self.home_page.setStyleSheet("")
        if hasattr(self, "bg_type_combo"):
            self.bg_type_combo.blockSignals(True)
            self.bg_type_combo.setCurrentIndex(0)  # "Фон Колір"
            self.bg_type_combo.blockSignals(False)
            if hasattr(self, "_bg_color_hint"): self._bg_color_hint.setVisible(True)
            if hasattr(self, "_bg_file_row"): self._bg_file_row.setVisible(False)
            if hasattr(self, "_bg_file_label"): self._bg_file_label.setText("Не вибрано")
        self._apply_bg_type()

        # Кнопки сайдбару
        for attr, btn_attr in [("chk_show_accounts_btn", "btn_accounts"),
                                ("chk_show_folder_btn", "btn_folder"),
                                ("chk_show_screens_btn", "btn_screens")]:
            if hasattr(self, attr): getattr(self, attr).setChecked(True)
            if hasattr(self, btn_attr): getattr(self, btn_attr).setVisible(True)

        # RAM
        if hasattr(self, "ram_slider"): self.ram_slider.setValue(2)

        # JVM
        if hasattr(self, "jvm_args_input"): self.jvm_args_input.setText("")

        # Приховати на запуск
        if hasattr(self, "chk_hide_on_launch"): self.chk_hide_on_launch.setChecked(False)

        # UI Style
        self._ui_style = "G9 UI"
        if hasattr(self, "ui_style_combo"):
            self.ui_style_combo.setCurrentIndex(0)

        # Snapshots
        self._show_snapshots = True
        if hasattr(self, "chk_show_snapshots"):
            self.chk_show_snapshots.setChecked(True)
        self.refresh_version_combo()

        # Sidebar order
        default_order = ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти", "🌐 Сайт"]
        self._sidebar_button_order = default_order
        if hasattr(self, "sidebar_order_list"):
            self.sidebar_order_list.clear()
            for name in default_order:
                self.sidebar_order_list.addItem(name)
        self._apply_sidebar_order()

        # Discord
        if hasattr(self, "chk_discord_rpc"):
            self.chk_discord_rpc.setChecked(True)
            self.discord.enabled = True
            self.discord.reconnect_if_needed()

        # Розмір вікна
        self.resize(900, 600)

        # Оновити preview кольорів
        for attr, dflt in [("_color_accent","#4caf50"),("_color_sidebar","#212121"),
                            ("_color_bg","#2b2b2b"),("_color_text","#ffffff")]:
            preview = getattr(self, attr + "_preview", None)
            if preview:
                c = getattr(self, attr, dflt)
                preview.setStyleSheet(f"background: {c}; border-radius:5px; border:1px solid #555;")

        self._apply_palette()
        self.save_settings()
        QMessageBox.information(self, "Скидання завершено", "Всі налаштування скинуто до стандартних.")

    # ── SETTINGS SAVE / LOAD ──
    def save_settings(self):
        try:
            data = {
                "last_nick": self.nick_dialog.current_nick,
                "last_version": self._current_version_text(),
                "bg_path": getattr(self, "_bg_path", ""),
                "bg_type": self.bg_type_combo.currentText() if hasattr(self, "bg_type_combo") else "Фон Колір",
                "ram": self.ram_slider.value() if hasattr(self, "ram_slider") else 2,
                "jvm_args": self.jvm_args_input.text() if hasattr(self, "jvm_args_input") else "",
                "hide_on_launch": self.chk_hide_on_launch.isChecked() if hasattr(self, "chk_hide_on_launch") else False,
                "auto_update": self.chk_auto_update.isChecked() if hasattr(self, "chk_auto_update") else True,
                "color_accent":  getattr(self, "_color_accent",  "#4caf50"),
                "color_titlebar": getattr(self, "_color_titlebar", "#212121"),
                "color_sidebar": getattr(self, "_color_sidebar", "#212121"),
                "color_bg":      getattr(self, "_color_bg",      "#2b2b2b"),
                "color_text":    getattr(self, "_color_text",    "#ffffff"),
                "ui_font_family": getattr(self, "_ui_font_family", "Segoe UI"),
                "ui_font_size":   getattr(self, "_ui_font_size",   10),
                "show_accounts_btn": self.chk_show_accounts_btn.isChecked() if hasattr(self, "chk_show_accounts_btn") else True,
                "show_folder_btn": self.chk_show_folder_btn.isChecked() if hasattr(self, "chk_show_folder_btn") else True,
                "show_screens_btn": self.chk_show_screens_btn.isChecked() if hasattr(self, "chk_show_screens_btn") else True,
                "discord_rpc_enabled": self.chk_discord_rpc.isChecked() if hasattr(self, "chk_discord_rpc") else True,
                "window_width": self.width(),
                "window_height": self.height(),
                "sidebar_button_order": getattr(self, "_sidebar_button_order", []),
                "show_snapshots": self.chk_show_snapshots.isChecked() if hasattr(self, "chk_show_snapshots") else True,
                "show_news": self.chk_show_news.isChecked() if hasattr(self, "chk_show_news") else True,
                "ui_style": getattr(self, "_ui_style", "G9 UI"),
            }
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"save_settings error: {e}")
 
    def load_settings(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
 
            last = data.get("last_version", "")
            for i in range(self.version_combo.count()):
                if self.version_combo.itemText(i).strip().lstrip("✔").strip() == last:
                    self.version_combo.setCurrentIndex(i)
                    break
 
            bg = data.get("bg_path", "")
            if bg and os.path.exists(bg):
                self._bg_path = bg

            # Restore background type
            bg_type = data.get("bg_type", "Фон Колір")
            if hasattr(self, "bg_type_combo"):
                idx_bg = self.bg_type_combo.findText(bg_type)
                if idx_bg >= 0:
                    self.bg_type_combo.blockSignals(True)
                    self.bg_type_combo.setCurrentIndex(idx_bg)
                    self.bg_type_combo.blockSignals(False)
                if hasattr(self, "_bg_color_hint"):
                    self._bg_color_hint.setVisible(bg_type == "Фон Колір")
                if hasattr(self, "_bg_file_row"):
                    self._bg_file_row.setVisible(bg_type == "Ваш Фон")
                if bg and hasattr(self, "_bg_file_label"):
                    self._bg_file_label.setText(os.path.basename(bg))
            QTimer.singleShot(120, self._apply_bg_type)

            if hasattr(self, "ram_slider"):
                self.ram_slider.setValue(data.get("ram", 2))
            if hasattr(self, "jvm_args_input"):
                self.jvm_args_input.setText(data.get("jvm_args", ""))
            if hasattr(self, "chk_hide_on_launch"):
                self.chk_hide_on_launch.setChecked(data.get("hide_on_launch", True))
            if hasattr(self, "chk_auto_update"):
                self.chk_auto_update.setChecked(data.get("auto_update", True))
 

            self._color_accent   = data.get("color_accent",  "#4caf50")
            self._color_titlebar = data.get("color_titlebar", "#212121")
            self._color_sidebar = data.get("color_sidebar", "#212121")
            self._color_bg      = data.get("color_bg",      "#2b2b2b")
            self._color_text    = data.get("color_text",    "#ffffff")
            self._ui_font_family = data.get("ui_font_family", "Segoe UI")
            self._ui_font_size   = data.get("ui_font_size",   10)
 
            # Restore font size slider (block signals to avoid palette recursion)
            if hasattr(self, "font_size_slider"):
                self.font_size_slider.blockSignals(True)
                self.font_size_slider.setValue(self._ui_font_size)
                self.font_size_slider.blockSignals(False)
                if hasattr(self, "font_size_lbl"):
                    self.font_size_lbl.setText(f"{self._ui_font_size} pt")
            if hasattr(self, "font_combo"):
                self.font_combo.blockSignals(True)
                idx = self.font_combo.findText(self._ui_font_family)
                if idx >= 0: self.font_combo.setCurrentIndex(idx)
                self.font_combo.blockSignals(False)
 
            # Always apply palette on load to restore font+color
            QTimer.singleShot(0, self._apply_palette)
 

            # Restore sidebar button visibility
            show_accounts = data.get("show_accounts_btn", True)
            if hasattr(self, "chk_show_accounts_btn"):
                self.chk_show_accounts_btn.setChecked(show_accounts)
            if hasattr(self, "btn_accounts"):
                self.btn_accounts.setVisible(show_accounts)
 
            show_folder = data.get("show_folder_btn", True)
            if hasattr(self, "chk_show_folder_btn"):
                self.chk_show_folder_btn.setChecked(show_folder)
            if hasattr(self, "btn_folder"):
                self.btn_folder.setVisible(show_folder)
 
            show_screens = data.get("show_screens_btn", True)
            if hasattr(self, "chk_show_screens_btn"):
                self.chk_show_screens_btn.setChecked(show_screens)
            if hasattr(self, "btn_screens"):
                self.btn_screens.setVisible(show_screens)
 
            # Restore sidebar order
            saved_order = data.get("sidebar_button_order", [])
            if saved_order:
                self._sidebar_button_order = saved_order
                if hasattr(self, "sidebar_order_list"):
                    self.sidebar_order_list.clear()
                    for name in saved_order:
                        self.sidebar_order_list.addItem(name)
                QTimer.singleShot(50, self._apply_sidebar_order)

            # Restore news toggle
            show_news = data.get("show_news", True)
            self._show_news = show_news
            if hasattr(self, "chk_show_news"):
                self.chk_show_news.setChecked(show_news)
            if hasattr(self, "news_panel"):
                self.news_panel.setVisible(show_news)

            # Restore snapshots toggle
            show_snaps = data.get("show_snapshots", True)
            self._show_snapshots = show_snaps
            if hasattr(self, "chk_show_snapshots"):
                self.chk_show_snapshots.setChecked(show_snaps)

            # Restore UI style
            ui_style = data.get("ui_style", "G9 UI")
            self._ui_style = ui_style
            if hasattr(self, "ui_style_combo"):
                idx_s = self.ui_style_combo.findText(ui_style)
                if idx_s >= 0: self.ui_style_combo.setCurrentIndex(idx_s)
            QTimer.singleShot(100, self._apply_ui_style)

            # Restore Discord RPC toggle
            discord_enabled = data.get("discord_rpc_enabled", True)
            if hasattr(self, "chk_discord_rpc"):
                self.chk_discord_rpc.setChecked(discord_enabled)
            self.discord.enabled = discord_enabled

            # Restore window size
            win_w = data.get("window_width", 900)
            win_h = data.get("window_height", 600)
            if win_w and win_h:
                self.resize(max(750, win_w), max(500, win_h))

            # Restore selected nick to all UI elements (fix: was resetting to "Player")
            saved_nick = data.get("last_nick", "")
            if saved_nick:
                self.nick_dialog.current_nick = saved_nick
                if hasattr(self, "btn_nick"):
                    self.btn_nick.setText(f"Нік: {saved_nick}")
                if hasattr(self, "skin_viewer_nick"):
                    self.skin_viewer_nick.setText(saved_nick)
 
        except Exception as e:
            print(f"load_settings error: {e}")
 
    # ── DRAG WINDOW ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Only drag via title bar area
            if self.title_bar.geometry().contains(event.pos()):
                self._old_pos = event.globalPos()
 
    def mouseMoveEvent(self, event):
        if self._old_pos:
            delta = event.globalPos() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPos()
 
    def mouseReleaseEvent(self, event):
        self._old_pos = None
 
    def closeEvent(self, event):
        self.discord.clear()
        self.save_settings()
        event.accept()
 
 
# ─────────────────────────── MAIN ───────────────────────────
if __name__ == '__main__':
    # Встановлюємо AppUserModelID ДО створення вікна — фікс іконки на панелі задач
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ALFA.G9Launcher.1.5")
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_THEME)
 
    splash = SplashScreen()
    screen = app.primaryScreen().geometry()
    splash.move(
        screen.center().x() - splash.width() // 2,
        screen.center().y() - splash.height() // 2
    )
    splash.show()
 
    STAGES = [
        (0,   "Ініціалізація..."),
        (30,  "Завантаження компонентів..."),
        (65,  "Підготовка лаунчера..."),
        (90,  "Майже готово..."),
        (100, "Запуск!"),
    ]
    _stage = [0]
 
    def advance_splash():
        idx = _stage[0]
        if idx >= len(STAGES):
            return
        val, msg = STAGES[idx]
        splash.set_status(msg)
        anim = QPropertyAnimation(splash.progress, b"value")
        anim.setDuration(280)
        anim.setStartValue(splash.progress.value())
        anim.setEndValue(val)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        splash._pb_anim = anim
        _stage[0] += 1
        if _stage[0] < len(STAGES):
            QTimer.singleShot(320, advance_splash)
        else:
            QTimer.singleShot(250, do_launch)
 
    def do_launch():
        window = G9Launcher()
        w, h = 900, 600
        cx = screen.center().x() - w // 2
        cy = screen.center().y() - h // 2
        window.move(cx, cy + 30)
        window.show()
        window.setWindowOpacity(0.0)
 
        fade = QPropertyAnimation(window, b"windowOpacity")
        fade.setDuration(380)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()
        window._fade_anim = fade
 
        slide = QPropertyAnimation(window, b"pos")
        slide.setDuration(380)
        slide.setStartValue(window.pos())
        slide.setEndValue(QPoint(cx, cy))
        slide.setEasingCurve(QEasingCurve.OutCubic)
        slide.start()
        window._slide_anim = slide
 
        splash.fade_out(splash.close)
        # Автоперевірка оновлень через 2 сек після старту (якщо ввімкнено)
        def _auto_update_check():
            if getattr(window.chk_auto_update, "isChecked", lambda: True)():
                window.check_for_update_now(silent=True)
        QTimer.singleShot(2000, _auto_update_check)
 
    QTimer.singleShot(200, advance_splash)
    sys.exit(app.exec_())