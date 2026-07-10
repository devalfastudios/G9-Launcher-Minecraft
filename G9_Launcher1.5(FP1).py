import sys
import uuid
import os
import shutil
import json
import re
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
                             QCheckBox, QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QDialog, QFileDialog, QGroupBox, QFormLayout,
                             QScrollArea, QSizePolicy, QFrame, QColorDialog,
                             QSizeGrip, QTabWidget, QAbstractItemView, QProgressDialog)
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
SKINS_DIR = os.path.join(CONFIG_DIR, 'skins')
INSTANCES_FILE = os.path.join(CONFIG_DIR, 'instances.json')
INSTANCES_DIR = os.path.join(CONFIG_DIR, 'instances')


# ─────────────────────────── ЗБІРКИ (INSTANCES) ───────────────────────────
def load_instances():
    """Завантажує список усіх створених збірок (як у FCL/PojavLauncher)."""
    if not os.path.isfile(INSTANCES_FILE):
        return []
    try:
        with open(INSTANCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_instances(instances_list):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(INSTANCES_FILE, "w", encoding="utf-8") as f:
            json.dump(instances_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_instance_dir(instance_name):
    safe_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in instance_name).strip()
    return os.path.join(INSTANCES_DIR, safe_name)


def add_instance(name, mc_version, loader, ram_gb=2, jvm_args=""):
    """Створює нову збірку: запис у instances.json + папка під моди/конфіги."""
    instances = load_instances()
    if any(i["name"] == name for i in instances):
        return False, "Збірка з такою назвою вже існує."
    instances.append({
        "name": name,
        "mc_version": mc_version,
        "loader": loader or "vanilla",
        "ram_gb": ram_gb,
        "jvm_args": jvm_args,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_instances(instances)
    inst_dir = get_instance_dir(name)
    os.makedirs(os.path.join(inst_dir, "mods"), exist_ok=True)
    os.makedirs(os.path.join(inst_dir, "saves"), exist_ok=True)
    os.makedirs(os.path.join(inst_dir, "config"), exist_ok=True)
    return True, inst_dir


def delete_instance(name, delete_files=False):
    instances = load_instances()
    instances = [i for i in instances if i["name"] != name]
    save_instances(instances)
    if delete_files:
        inst_dir = get_instance_dir(name)
        try:
            if os.path.isdir(inst_dir):
                shutil.rmtree(inst_dir)
        except Exception:
            pass


def get_instance_by_name(name):
    for i in load_instances():
        if i["name"] == name:
            return i
    return None


def get_local_skin_path(nick):
    """Повертає шлях до локально завантаженого скіна для цього ніка, або None."""
    try:
        safe_nick = "".join(c for c in nick if c not in '<>:"/\\|?*').strip()
        path = os.path.join(SKINS_DIR, f"{safe_nick}.png")
        return path if os.path.isfile(path) else None
    except Exception:
        return None


def set_local_skin_path(nick, source_file):
    """Копіює обраний PNG-файл скіна у внутрішню папку skins/ під ім'я ніка."""
    try:
        os.makedirs(SKINS_DIR, exist_ok=True)
        safe_nick = "".join(c for c in nick if c not in '<>:"/\\|?*').strip()
        dest = os.path.join(SKINS_DIR, f"{safe_nick}.png")
        shutil.copy2(source_file, dest)
        return dest
    except Exception:
        return None


def remove_local_skin(nick):
    """Видаляє локально завантажений скін для ніка (повертається до minotar.net)."""
    try:
        safe_nick = "".join(c for c in nick if c not in '<>:"/\\|?*').strip()
        path = os.path.join(SKINS_DIR, f"{safe_nick}.png")
        if os.path.isfile(path):
            os.remove(path)
            return True
    except Exception:
        pass
    return False

# ─────────────────────────── AUTO-UPDATE INFRASTRUCTURE ───────────────────────────
_LAUNCHER_VERSION = "1.5-fp1"
_UPDATE_REPO = "devalfastudios/G9-Launcher-Minecraft"  # Новий репозиторій
_UPDATE_API  = f"https://api.github.com/repos/{_UPDATE_REPO}/releases/latest"
_UPDATE_CACHE_FILE = os.path.join(
    os.getenv('APPDATA', os.path.expanduser('~')), '.g9launcher', '_update_cache.json'
)

def _fetch_latest_release_info():
    """Завантажує інформацію про останній реліз з GitHub API. Повертає dict або None.
    Таймаут зменшено до 3с — якщо GitHub/мережа недоступні, не змушуємо
    користувача чекати довго на результат перевірки."""
    try:
        req = urllib.request.Request(
            _UPDATE_API,
            headers={
                "User-Agent": f"G9Launcher/{_LAUNCHER_VERSION}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception:
        return None

def _parse_version_tag(tag: str):
    """
    Розбирає тег версії формату G9 Launcher на порівнюваний кортеж.
    Підтримує: "1.5", "1.5-fp1", "1.5-fp12", "1.5.1" (про всяк випадок).
    Повертає (major, minor, fp_number) де fp_number=0 для "чистої" версії
    без FP — так "1.5" < "1.5-fp1" < "1.5-fp2" < "1.6".
    """
    t = tag.strip().lstrip("vV").strip()
    fp_num = 0
    # Витягуємо "-fpN" або "-FPN" суфікс, якщо є
    m = re.search(r"-fp(\d+)$", t, re.IGNORECASE)
    if m:
        fp_num = int(m.group(1))
        t = t[:m.start()]
    # Залишок має бути "x.y" або "x.y.z" — беремо як числа
    nums = []
    for part in t.split("."):
        part = "".join(ch for ch in part if ch.isdigit())
        if part:
            nums.append(int(part))
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3]) + (fp_num,)


def _is_newer_version(remote: str, local: str) -> bool:
    """
    Повертає True якщо remote > local.
    Підтримує формат G9 Launcher: "1.5" < "1.5-fp1" < "1.5-fp2" < "1.6".
    """
    try:
        return _parse_version_tag(remote) > _parse_version_tag(local)
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
    """
    Невидимий маркер зміни розміру для конкретного краю/кута вікна.
    Без будь-якої візуальної індикації — просто зона для захоплення мишею.
    Підтримує всі кути і краї КРІМ правого верхнього (там — кнопки управління вікном).
    """
    # edge: 'bottom','right','left','bottom-left','bottom-right','top-left'
    def __init__(self, parent, edge='bottom-right', thickness=8):
        super().__init__(parent)
        self._edge = edge
        self._thickness = thickness
        self._resizing = False
        self._start_pos = None
        self._start_geom = None

        cursor_map = {
            'bottom':       Qt.SizeVerCursor,
            'right':        Qt.SizeHorCursor,
            'left':         Qt.SizeHorCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'bottom-left':  Qt.SizeBDiagCursor,
            'top-left':     Qt.SizeFDiagCursor,
        }
        self.setCursor(cursor_map.get(edge, Qt.SizeAllCursor))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def paintEvent(self, event):
        pass  # Повністю невидимий

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._start_pos = event.globalPos()
            self._start_geom = self.window().geometry()

    def mouseMoveEvent(self, event):
        if not (self._resizing and self._start_pos):
            return
        delta = event.globalPos() - self._start_pos
        geo = self._start_geom
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        dx, dy = delta.x(), delta.y()
        MIN_W, MIN_H = 750, 500

        edge = self._edge
        if edge == 'bottom':
            h = max(MIN_H, h + dy)
        elif edge == 'right':
            w = max(MIN_W, w + dx)
        elif edge == 'left':
            new_w = max(MIN_W, w - dx)
            x = x + (w - new_w)
            w = new_w
        elif edge == 'bottom-right':
            w = max(MIN_W, w + dx)
            h = max(MIN_H, h + dy)
        elif edge == 'bottom-left':
            new_w = max(MIN_W, w - dx)
            x = x + (w - new_w)
            w = new_w
            h = max(MIN_H, h + dy)
        elif edge == 'top-left':
            new_w = max(MIN_W, w - dx)
            new_h = max(MIN_H, h - dy)
            x = x + (w - new_w)
            y = y + (h - new_h)
            w, h = new_w, new_h

        win = self.window()
        win.setGeometry(x, y, w, h)
        try:
            win._update_scale()
        except Exception:
            pass

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
# ─────────────────────── ПІДТВЕРДЖЕННЯ З ТАЙМЕРОМ ───────────────────────
class CountdownConfirmDialog(QDialog):
    """
    Діалог підтвердження небезпечної дії з обов'язковою затримкою.
    Кнопка підтвердження стає активною тільки після завершення відліку
    (за замовчуванням 10 секунд), щоб виключити випадкове натискання.
    """
    def __init__(self, parent, title, message, confirm_text="Підтвердити",
                 seconds=10, danger=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setModal(True)
        self._seconds_left = seconds
        self._confirmed = False

        self.setStyleSheet(
            "QDialog { background: #1e1e1e; }"
            "QLabel { background: transparent; color: #e8e8e8; }"
        )

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(22, 20, 22, 18)
        vlay.setSpacing(14)

        icon_lbl = QLabel("\u26a0\ufe0f" if danger else "\u2753")
        icon_lbl.setStyleSheet("font-size: 30px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        vlay.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setStyleSheet("color: #ddd; font-size: 13px; background: transparent;")
        vlay.addWidget(msg_lbl)

        btn_row = QHBoxLayout()
        self.btn_cancel = QPushButton("Скасувати")
        self.btn_cancel.setStyleSheet(
            "background: #444; color: white; border-radius: 8px; padding: 9px 18px;")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = QPushButton(f"{confirm_text} ({self._seconds_left}с)")
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.setStyleSheet(
            "QPushButton { background: #555; color: #999; border-radius: 8px; padding: 9px 18px; font-weight: bold; }"
        )
        self._confirm_text = confirm_text
        self.btn_confirm.clicked.connect(self._on_confirm)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_confirm)
        vlay.addLayout(btn_row)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        self._seconds_left -= 1
        if self._seconds_left <= 0:
            self._timer.stop()
            self.btn_confirm.setEnabled(True)
            self.btn_confirm.setText(self._confirm_text)
            self.btn_confirm.setStyleSheet(
                "QPushButton { background: #c62828; color: white; border-radius: 8px; "
                "padding: 9px 18px; font-weight: bold; }"
                "QPushButton:hover { background: #e53935; }"
            )
        else:
            self.btn_confirm.setText(f"{self._confirm_text} ({self._seconds_left}с)")

    def _on_confirm(self):
        self._confirmed = True
        self.accept()

    @staticmethod
    def ask(parent, title, message, confirm_text="Підтвердити", seconds=10, danger=True):
        """Показує діалог і повертає True, якщо користувач підтвердив дію."""
        dlg = CountdownConfirmDialog(parent, title, message, confirm_text, seconds, danger)
        dlg.exec_()
        return dlg._confirmed


class InstanceModsDialog(QDialog):
    """Просте керування модами (.jar) обраної збірки — список + додати/видалити файл."""
    def __init__(self, parent, instance_data):
        super().__init__(parent)
        self.instance_data = instance_data
        self.setWindowTitle(f"Моди: {instance_data['name']}")
        self.setMinimumSize(420, 380)
        self.setModal(True)
        self.setStyleSheet(
            "QDialog { background: #1e1e1e; }"
            "QLabel { background: transparent; color: #e8e8e8; }"
            "QListWidget { background:#252525; border:1px solid #444; border-radius:6px; color:#ddd; }"
            "QPushButton { border-radius: 8px; padding: 8px 16px; font-weight: bold; }"
        )

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 18, 20, 16)
        vlay.setSpacing(12)

        loader_name = (instance_data.get("loader") or "vanilla").capitalize()
        info_lbl = QLabel(
            f"📦 <b>{instance_data['name']}</b>  —  "
            f"Minecraft {instance_data['mc_version']} ({loader_name})"
        )
        info_lbl.setStyleSheet("background:#252525; border-radius:8px; padding:10px; font-size:12px;")
        vlay.addWidget(info_lbl)

        mods_lbl = QLabel("МОДИ (.jar):")
        mods_lbl.setStyleSheet("color:#888; font-size:11px; font-weight:bold; background:transparent;")
        vlay.addWidget(mods_lbl)

        self.mods_list = QListWidget()
        vlay.addWidget(self.mods_list, 1)
        self._refresh_mods_list()

        mods_btn_row = QHBoxLayout()
        btn_add_mod = QPushButton("➕ Додати мод")
        btn_add_mod.setStyleSheet("background:#1565c0; color:white;")
        btn_add_mod.clicked.connect(self._add_mod)
        btn_remove_mod = QPushButton("🗑 Видалити обраний")
        btn_remove_mod.setStyleSheet("background:#555; color:#ddd;")
        btn_remove_mod.clicked.connect(self._remove_selected_mod)
        mods_btn_row.addWidget(btn_add_mod)
        mods_btn_row.addWidget(btn_remove_mod)
        vlay.addLayout(mods_btn_row)

        btn_close = QPushButton("Закрити")
        btn_close.setStyleSheet("background:#444; color:white;")
        btn_close.clicked.connect(self.accept)
        vlay.addWidget(btn_close, 0, Qt.AlignRight)

    def _mods_dir(self):
        return os.path.join(get_instance_dir(self.instance_data["name"]), "mods")

    def _refresh_mods_list(self):
        self.mods_list.clear()
        mods_dir = self._mods_dir()
        if not os.path.isdir(mods_dir):
            return
        jars = [f for f in os.listdir(mods_dir) if f.lower().endswith(".jar")]
        if not jars:
            self.mods_list.addItem("(модів ще немає)")
            return
        for j in sorted(jars):
            self.mods_list.addItem(j)

    def _add_mod(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Обрати файли модів (.jar)", "", "Mod files (*.jar)")
        if not files:
            return
        mods_dir = self._mods_dir()
        os.makedirs(mods_dir, exist_ok=True)
        copied = 0
        for f in files:
            try:
                shutil.copy2(f, os.path.join(mods_dir, os.path.basename(f)))
                copied += 1
            except Exception:
                pass
        self._refresh_mods_list()
        if copied:
            QMessageBox.information(self, "Готово", f"Додано {copied} мод(ів) до збірки.")

    def _remove_selected_mod(self):
        item = self.mods_list.currentItem()
        if not item or item.text().startswith("("):
            return
        mods_dir = self._mods_dir()
        path = os.path.join(mods_dir, item.text())
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass
        self._refresh_mods_list()


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
        """Спочатку перевіряємо, чи є локально завантажений скін для цього ніка —
        якщо є, показуємо його (вирізаючи голову з повного skin.png 64x64).
        Інакше тягнемо хелм з minotar.net (онлайн-скін за ніком)."""
        local_path = get_local_skin_path(nick)
        if local_path and os.path.isfile(local_path):
            self._load_local_head(local_path)
            return

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

    def _load_local_head(self, path):
        """Вирізає голову (8x8 px, область 8,8) з локального файлу skin.png і масштабує."""
        try:
            img = QImage(path)
            if img.isNull():
                return
            # Стандартний формат скіна Minecraft: голова — квадрат 8x8 у координатах (8,8)
            # Підтримуємо як 64x64 (новий формат), так і 64x32 (старий) — голова в обох однакова.
            scale = img.width() / 64.0 if img.width() >= 64 else 1.0
            x = int(8 * scale)
            y = int(8 * scale)
            size = int(8 * scale)
            head = img.copy(x, y, size, size)
            pix = QPixmap.fromImage(head).scaled(
                80, 80, Qt.KeepAspectRatio, Qt.FastTransformation)
            self._set_pixmap(pix)
        except Exception:
            pass

    def load_full_skin_preview(self, path):
        """Показує мініатюру повного скіна (для попереднього перегляду у вікні вибору файлу)."""
        try:
            img = QImage(path)
            if img.isNull():
                return False
            pix = QPixmap.fromImage(img).scaled(
                80, 80, Qt.KeepAspectRatio, Qt.FastTransformation)
            self._set_pixmap(pix)
            return True
        except Exception:
            return False

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


def _get_java_version_string(java_exe):
    """Повертає рядок версії для конкретного java.exe, або None."""
    try:
        r = _run_hidden([java_exe, "-version"], capture_output=True, text=True, timeout=5)
        line = (r.stderr or r.stdout).split("\n")[0]
        return line.replace("java version", "").replace("openjdk version", "").strip().strip('"').strip("'")
    except Exception:
        return None


def _is_windows_store_stub(path):
    """
    На Windows shutil.which('java') часто повертає шлях до App Execution Alias —
    заглушку у WindowsApps, яка не є справжньою Java і при виклику відкриває
    Microsoft Store замість виводу версії. Її потрібно ігнорувати.
    """
    try:
        norm = path.replace("/", "\\").lower()
        return "\\windowsapps\\" in norm
    except Exception:
        return False


def find_all_installed_java():
    """
    Шукає всі встановлені на системі Java (включно з Mojang runtime).
    Повертає список dict: {"path": ..., "version": ..., "source": ...}
    Використовує прямий пошук без рекурсивного os.walk — щоб не зависати.
    """
    results = []
    seen_paths = set()

    def _add(path, source):
        if not path:
            return
        # Нормалізуємо шлях
        try:
            norm = os.path.normcase(os.path.abspath(path))
        except Exception:
            return
        if norm in seen_paths:
            return
        if not os.path.isfile(path):
            return
        if _is_windows_store_stub(path):
            return
        seen_paths.add(norm)
        ver = _get_java_version_string(path)
        if ver:
            results.append({"path": path, "version": ver, "source": source})

    # 1) Системна java (фільтруємо WindowsApps-заглушку Microsoft)
    for candidate in ["java", "javaw"]:
        found = shutil.which(candidate)
        if found and not _is_windows_store_stub(found):
            _add(found, "Системна (PATH)")
            break

    # 2) JAVA_HOME
    jh = os.environ.get("JAVA_HOME", "")
    if jh:
        for exe_name in ("javaw.exe", "java.exe", "java"):
            exe = os.path.join(jh, "bin", exe_name)
            if os.path.isfile(exe):
                _add(exe, "JAVA_HOME")
                break

    if os.name == "nt":
        # 3) Стандартні місця встановлення Windows (прямий пошук без os.walk)
        search_roots = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Eclipse Foundation",
            r"C:\Program Files\Microsoft",
            r"C:\Program Files\Zulu",
            r"C:\Program Files\BellSoft",
            r"C:\Program Files\Amazon Corretto",
            r"C:\Program Files\Semeru",
            r"C:\Program Files\OpenJDK",
        ]
        for root_dir in search_roots:
            if not os.path.isdir(root_dir):
                continue
            try:
                for entry in os.listdir(root_dir):
                    entry_dir = os.path.join(root_dir, entry)
                    if not os.path.isdir(entry_dir):
                        continue
                    bin_dir = os.path.join(entry_dir, "bin")
                    for exe_name in ("javaw.exe", "java.exe"):
                        exe = os.path.join(bin_dir, exe_name)
                        if os.path.isfile(exe):
                            _add(exe, f"{entry} ({os.path.basename(root_dir)})")
                            break
            except Exception:
                pass

        # 4) Windows Registry (найнадійніший спосіб на Windows)
        try:
            import winreg
            for reg_path in [
                r"SOFTWARE\JavaSoft\Java Runtime Environment",
                r"SOFTWARE\JavaSoft\Java Development Kit",
                r"SOFTWARE\JavaSoft\JDK",
                r"SOFTWARE\WOW6432Node\JavaSoft\Java Runtime Environment",
                r"SOFTWARE\WOW6432Node\JavaSoft\JDK",
            ]:
                for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    try:
                        key = winreg.OpenKey(hive, reg_path)
                        i = 0
                        while True:
                            try:
                                ver_name = winreg.EnumKey(key, i)
                                ver_key = winreg.OpenKey(key, ver_name)
                                home, _ = winreg.QueryValueEx(ver_key, "JavaHome")
                                for exe_name in ("javaw.exe", "java.exe"):
                                    exe = os.path.join(home, "bin", exe_name)
                                    if os.path.isfile(exe):
                                        _add(exe, f"Registry JRE {ver_name}")
                                        break
                                winreg.CloseKey(ver_key)
                                i += 1
                            except OSError:
                                break
                        winreg.CloseKey(key)
                    except OSError:
                        pass
        except ImportError:
            pass  # winreg доступний тільки на Windows

    # 5) Mojang runtime (прямий пошук без os.walk)
    try:
        runtime_dir = os.path.join(CONFIG_DIR, "runtime")
        if os.path.isdir(runtime_dir):
            for component in os.listdir(runtime_dir):
                comp_base = os.path.join(runtime_dir, component)
                if not os.path.isdir(comp_base):
                    continue
                # Структура: runtime/<component>/<platform>/<component>/bin/
                for platform_dir in os.listdir(comp_base):
                    bin_dir = os.path.join(comp_base, platform_dir, component, "bin")
                    for exe_name in ("javaw.exe", "java.exe", "java"):
                        exe = os.path.join(bin_dir, exe_name)
                        if os.path.isfile(exe):
                            _add(exe, f"Mojang Runtime — {component}")
                            break
    except Exception:
        pass

    return results


def _prefer_javaw(java_exe):
    """
    Якщо поруч існує javaw.exe (Windows, без консольного вікна) —
    використовуємо його замість java.exe. Це той самий JVM, просто без
    видимого чорного вікна консолі, і НЕ впливає на головне вікно гри
    (на відміну від приховування всього процесу через STARTUPINFO).
    """
    if not java_exe or os.name != "nt":
        return java_exe
    if java_exe.lower().endswith("javaw.exe"):
        return java_exe
    candidate = os.path.join(os.path.dirname(java_exe), "javaw.exe")
    return candidate if os.path.isfile(candidate) else java_exe


def _ensure_java_runtime(mc_ver, minecraft_directory):
    """
    Автоматично підбирає і (за потреби) встановлює правильний Mojang JRE
    для конкретної версії Minecraft, замість покладатися на системну Java.
    Повертає шлях до java executable, або None якщо не вдалось.
    """
    try:
        version_json_path = os.path.join(
            minecraft_directory, "versions", mc_ver, f"{mc_ver}.json")
        required_runtime = None
        if os.path.isfile(version_json_path):
            with open(version_json_path, "r", encoding="utf-8") as f:
                vdata = json.load(f)
            required_runtime = (vdata.get("javaVersion", {}) or {}).get("component")

        if not required_runtime:
            try:
                major = int(mc_ver.split(".")[1]) if mc_ver.count(".") >= 1 and mc_ver[0].isdigit() else 99
            except Exception:
                major = 99
            if major >= 18:
                required_runtime = "java-runtime-gamma"
            elif major >= 17:
                required_runtime = "java-runtime-alpha"
            else:
                required_runtime = "jre-legacy"

        try:
            minecraft_launcher_lib.runtime.install_jvm_runtime(
                required_runtime, minecraft_directory)
        except Exception:
            pass

        java_exe = minecraft_launcher_lib.runtime.get_executable_path(
            required_runtime, minecraft_directory)
        if java_exe and os.path.isfile(java_exe):
            return _prefer_javaw(java_exe)
    except Exception:
        pass
    return None


_LEGACY_AUDIO_VERSIONS = {"1.0", "1.1", "1.2.1", "1.2.2", "1.2.3", "1.2.4", "1.2.5",
                           "1.3.1", "1.3.2", "1.4.2", "1.4.4", "1.4.5", "1.4.6", "1.4.7",
                           "1.5", "1.5.1", "1.5.2", "1.6.1", "1.6.2", "1.6.4"}

def _needs_legacy_audio_fix(mc_ver):
    return mc_ver in _LEGACY_AUDIO_VERSIONS

def _fix_legacy_audio(mc_ver, assets_source_dir, game_dir=None, progress_cb=None):
    """
    Старі версії (до 1.6.4, включно з 1.6.1) очікують звукові файли у
    <CONFIG_DIR>/assets/virtual/legacy/..., а НЕ в <gameDir>/resources/.

    Це підтверджено реальною поведінкою офіційного Mojang launcher та
    самого minecraft_launcher_lib: команда запуску підставляє
    ${game_assets} = <CONFIG_DIR>/assets/virtual/legacy (бачимо це у
    вихідному коді command.py бібліотеки). Офіційний лаунчер сам
    "матеріалізує" (reconstruct) цю папку з сучасних assets/objects/
    за асет-індексом перед запуском старих версій — тут робимо те саме
    без звернення до вимкненого Amazon S3.

    game_dir більше не використовується для звуку (залишений у
    сигнатурі для зворотної сумісності викликів) — шлях завжди
    спільний у CONFIG_DIR, бо саме так його читає сам Minecraft-клієнт
    через --assetsDir/game_assets, незалежно від обраного gameDirectory.
    """
    try:
        assets_dir = os.path.join(assets_source_dir, "assets")
        indexes_dir = os.path.join(assets_dir, "indexes")
        objects_dir = os.path.join(assets_dir, "objects")
        # ── ПРАВИЛЬНИЙ шлях: assets/virtual/legacy, а НЕ resources/ у gameDir ──
        virtual_legacy_dir = os.path.join(assets_dir, "virtual", "legacy")

        if not os.path.isdir(indexes_dir) or not os.path.isdir(objects_dir):
            return False

        version_json_path = os.path.join(
            assets_source_dir, "versions", mc_ver, f"{mc_ver}.json")
        index_id = "legacy"
        if os.path.isfile(version_json_path):
            try:
                with open(version_json_path, "r", encoding="utf-8") as f:
                    vdata = json.load(f)
                index_id = (vdata.get("assetIndex", {}) or {}).get("id", "legacy")
            except Exception:
                pass

        index_path = os.path.join(indexes_dir, f"{index_id}.json")
        if not os.path.isfile(index_path):
            candidates = [f for f in os.listdir(indexes_dir)
                          if f.startswith(("legacy", "pre-1.6"))]
            if not candidates:
                return False
            index_path = os.path.join(indexes_dir, candidates[0])

        with open(index_path, "r", encoding="utf-8") as f:
            idx_data = json.load(f)
        objects = idx_data.get("objects", {})

        os.makedirs(virtual_legacy_dir, exist_ok=True)
        total = len(objects)
        done = 0
        copied = 0
        for rel_path, meta in objects.items():
            done += 1
            h = meta.get("hash", "")
            if not h:
                continue
            src = os.path.join(objects_dir, h[:2], h)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(virtual_legacy_dir, rel_path.replace("/", os.sep))
            if os.path.isfile(dst):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst)
                copied += 1
            except Exception:
                pass
            if progress_cb and total:
                progress_cb(int(done * 100 / total))
        return copied > 0
    except Exception:
        return False
 
 
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
    "26.3 Snapshot 3 - Snapshot",
    "26.3 Snapshot 2 - Snapshot",
    "26.3 Snapshot 1 - Snapshot",
]

# Таблиця відображення: назва у лаунчері → реальний Mojang version ID
DISPLAY_MAP = {
    # Стабільні релізи
    "26.2":                ("26.2",                None),
    "26.1.2":              ("26.1.2",              None),
    "26.1":                ("26.1",                None),
    # Снапшоти 26.3
    "26.3 Snapshot 3":     ("26.3-snapshot-3",     None),
    "26.3 Snapshot 2":     ("26.3-snapshot-2",     None),
    "26.3 Snapshot 1":     ("26.3-snapshot-1",     None),
}

# ─────────────────────────── NEWS FEED ───────────────────────────
NEWS_FEED_URL = "https://devalfastudios.github.io/G9-Launcher/news.json"

# Fallback static news shown if network is unavailable
NEWS_FALLBACK = [
    {
        "title": "G9 Launcher v1.5 FP 1",
        "summary": "Fix Pack 1: виправлено консольне вікно при запуску гри, виправлено збереження даних гри (ізоляція тепер по версії MC без лоадера), список встановлених Java — пошук через реєстр Windows, виправлено кнопку перевірки оновлень на сторінці «Про програму», додано зміну розміру за всіма кутами вікна, новий снапшот 26.3 Snapshot 3.",
        "date": "03.07.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "Minecraft 26.3 Snapshot 3",
        "summary": "Вийшов 26.3 Snapshot 3 (7 липня 2026): соломʼяні ліжка, подушки 16 кольорів, кастомні рецепти варіння, нові пост-ефекти. Доступний у G9 Launcher у розділі Снапшоти.",
        "date": "07.07.2026",
        "image": "",
        "url": "https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-3"
    },
    {
        "title": "G9 Launcher v1.5",
        "summary": "G9 Launcher 1.5: автозапуск Windows, автоперевірка оновлень через GitHub, встановлення оновлень з лаунчера, фікс іконки на панелі задач, новий стиль Round UI, матеріал-дизайн у характеристиках, виправлення кнопки сайту.",
        "date": "15.06.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "G9 Launcher v1.4 FP 1",
        "summary": "G9 Launcher отримав виправлення: DISPLAY_MAP not defined при старті, оновлено снапшоти 26.2, виправлено запуск Java 25 для Minecraft 26.x.",
        "date": "13.06.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "G9 Launcher v1.4",
        "summary": "Нові функції: MetroUI стиль, порядок кнопок бокової панелі, більше шрифтів, Discord Rich Presence, покращення стилю.",
        "date": "25.05.2026",
        "image": "",
        "url": "https://devalfastudios.github.io/G9-Launcher/"
    },
    {
        "title": "Minecraft 26.2",
        "summary": "Minecraft 26.2 вже доступний у G9 Launcher. Оновлення додає нові блоки та можливості.",
        "date": "16.06.2026",
        "image": "",
        "url": "https://minecraft.net/"
    },
]

def fetch_news():
    """Повертає (list, None) — офлайн-режим, дані беруться з NEWS_FALLBACK."""
    return (NEWS_FALLBACK, None)

ALL_VERSIONS = [
    "26.2 - Vanilla", "26.2 - Forge", "26.2 - Fabric", "26.2 - NeoForge",
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
    "1.19.4 - Vanilla", "1.19.4 - Forge", "1.19.4 - Fabric",
    "1.19.3 - Vanilla", "1.19.3 - Forge", "1.19.3 - Fabric",
    "1.19.2 - Vanilla", "1.19.2 - Forge", "1.19.2 - Fabric",
    "1.19.1 - Vanilla", "1.19.1 - Forge", "1.19.1 - Fabric",
    "1.19 - Vanilla", "1.19 - Forge", "1.19 - Fabric",
    "1.18.2 - Vanilla", "1.18.2 - Forge", "1.18.2 - Fabric",
    "1.18.1 - Vanilla", "1.18.1 - Forge", "1.18.1 - Fabric",
    "1.18 - Vanilla", "1.18 - Forge", "1.18 - Fabric",
    "1.17.1 - Vanilla", "1.17.1 - Forge", "1.17.1 - Fabric",
    "1.17 - Vanilla", "1.17 - Forge", "1.17 - Fabric",
    "1.16.5 - Vanilla", "1.16.5 - Forge", "1.16.5 - Fabric",
    "1.16.4 - Vanilla", "1.16.4 - Forge", "1.16.4 - Fabric",
    "1.16.3 - Vanilla", "1.16.3 - Forge", "1.16.3 - Fabric",
    "1.16.2 - Vanilla", "1.16.2 - Forge", "1.16.2 - Fabric",
    "1.16.1 - Vanilla", "1.16.1 - Forge", "1.16.1 - Fabric",
    "1.16 - Vanilla", "1.16 - Forge", "1.16 - Fabric",
    "1.15.2 - Vanilla", "1.15.2 - Forge", "1.15.2 - Fabric",
    "1.15.1 - Vanilla", "1.15.1 - Forge", "1.15.1 - Fabric",
    "1.15 - Vanilla", "1.15 - Forge", "1.15 - Fabric",
    "1.14.4 - Vanilla", "1.14.4 - Forge", "1.14.4 - Fabric",
    "1.14.3 - Vanilla", "1.14.3 - Forge", "1.14.3 - Fabric",
    "1.14.2 - Vanilla", "1.14.2 - Forge", "1.14.2 - Fabric",
    "1.14.1 - Vanilla", "1.14.1 - Forge", "1.14.1 - Fabric",
    "1.14 - Vanilla", "1.14 - Forge", "1.14 - Fabric",
    "1.13.2 - Vanilla", "1.13.2 - Forge",
    "1.13.1 - Vanilla", "1.13.1 - Forge",
    "1.13 - Vanilla", "1.13 - Forge",
    "1.12.2 - Vanilla", "1.12.2 - Forge",
    "1.12.1 - Vanilla", "1.12.1 - Forge",
    "1.12 - Vanilla", "1.12 - Forge",
    "1.11.2 - Vanilla", "1.11.2 - Forge",
    "1.11.1 - Vanilla", "1.11.1 - Forge",
    "1.11 - Vanilla", "1.11 - Forge",
    "1.10.2 - Vanilla", "1.10.2 - Forge",
    "1.10.1 - Vanilla", "1.10.1 - Forge",
    "1.10 - Vanilla", "1.10 - Forge",
    "1.9.4 - Vanilla", "1.9.4 - Forge",
    "1.9.2 - Vanilla", "1.9.2 - Forge",
    "1.9 - Vanilla", "1.9 - Forge",
    "1.8.9 - Vanilla", "1.8.9 - Forge",
    "1.8.8 - Vanilla", "1.8.8 - Forge",
    "1.8 - Vanilla", "1.8 - Forge",
    "1.7.10 - Vanilla", "1.7.10 - Forge",
    "1.7.9 - Vanilla", "1.7.9 - Forge",
    "1.7.2 - Vanilla", "1.7.2 - Forge",
    "1.6.4 - Vanilla", "1.6.4 - Forge",
    "1.6.2 - Vanilla", "1.6.2 - Forge",
    "1.6.1 - Vanilla", "1.6.1 - Forge",
    "1.5.2 - Vanilla", "1.5.2 - Forge",
    "1.5.1 - Vanilla", "1.5.1 - Forge",
    "1.5 - Vanilla", "1.5 - Forge",
    "1.4.7 - Vanilla", "1.4.7 - Forge",
    "1.4.6 - Vanilla", "1.4.6 - Forge",
    "1.4.5 - Vanilla", "1.4.5 - Forge",
    "1.4.4 - Vanilla", "1.4.4 - Forge",
    "1.4.2 - Vanilla", "1.4.2 - Forge",
    "1.3.2 - Vanilla", "1.3.2 - Forge",
    "1.3.1 - Vanilla", "1.3.1 - Forge",
    "1.2.5 - Vanilla", "1.2.5 - Forge",
    "1.2.4 - Vanilla", "1.2.4 - Forge",
    "1.2.3 - Vanilla", "1.2.3 - Forge",
    "1.2.2 - Vanilla", "1.2.2 - Forge",
    "1.2.1 - Vanilla", "1.2.1 - Forge",
    "1.1 - Vanilla", "1.1 - Forge",
    "1.0 - Vanilla", "1.0 - Forge",
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
        self.setWindowTitle("G9 Launcher v1.5")
        self.setMinimumSize(750, 500)
        self.resize(900, 600)
        self.is_playing = False
        self.nick_dialog = NickContainer()
        self._old_pos = None
        self.discord = DiscordRPC()
        self._base_w = 900
        self._base_h = 600
        self._base_font = 10
        # Ізоляція версій увімкнена за замовчуванням для всіх користувачів
        self._isolate_versions = True
 
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
        W, H = self.width(), self.height()
        T = 8
        if hasattr(self, "_resize_grips"):
            g = self._resize_grips
            # Нижній край (горизонтально між двома нижніми кутами)
            g['bottom'].setGeometry(T*2, H - T, W - T*4, T)
            # Правий край (вертикально, без перетину з правим верхнім кутом)
            g['right'].setGeometry(W - T, T*2, T, H - T*4)
            # Лівий край
            g['left'].setGeometry(0, T*2, T, H - T*4)
            # Нижній правий кут
            g['bottom-right'].setGeometry(W - T*2, H - T*2, T*2, T*2)
            # Нижній лівий кут
            g['bottom-left'].setGeometry(0, H - T*2, T*2, T*2)
            # Лівий верхній кут
            g['top-left'].setGeometry(0, 0, T*2, T*2)
            for grip_w in g.values():
                grip_w.raise_()
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
        prev = self.stacked_widget.currentIndex()
        if prev == index:
            return
        if index == 4:  # Specs page — remember where we came from
            self._specs_prev_page = prev
            self._update_specs_page()
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

        self.btn_instances = QPushButton("📦 Збірки")
        self.btn_instances.setMinimumHeight(38)
        self.btn_instances.clicked.connect(lambda: self.switch_page(6))

        self._side_layout = side_layout

        # ── BUTTONS CONTAINER (fixed position — news hide won't shift them) ──
        self._btns_container = QWidget()
        self._btns_container.setStyleSheet("background: transparent;")
        _btns_vbox = QVBoxLayout(self._btns_container)
        _btns_vbox.setContentsMargins(0, 0, 0, 0)
        _btns_vbox.setSpacing(4)
        for b in [self.btn_settings, self.btn_accounts,
                  self.btn_folder, self.btn_screens, self.btn_instances]:
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
        controls.setSpacing(10)

        self.version_combo = QComboBox()
        self.version_combo.setMaxVisibleItems(12)
        self.version_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.version_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.version_combo.setMinimumHeight(40)
        self.version_combo.setMinimumWidth(180)
        self.version_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.version_combo.currentIndexChanged.connect(self._on_version_changed)

        self.btn_nick = QPushButton("Нік: Player")
        self.btn_nick.setToolTip("Обрати акаунт")
        self.btn_nick.setMinimumHeight(40)
        self.btn_nick.clicked.connect(lambda: self.switch_page(3))

        self.btn_play = QPushButton("▶  Грати")
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.setMinimumHeight(50)
        self.btn_play.setMinimumWidth(160)
        self.btn_play.clicked.connect(self.toggle_play)

        controls.addWidget(self.version_combo, 1)
        controls.addWidget(self.btn_nick)
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
 
        # ── Page 4: Full-screen Specifications ──
        self.specs_page = QWidget()
        self.init_specs_page()
        self.stacked_widget.addWidget(self.specs_page)     # index 4

        # ── Page 5: News reader ──
        self.news_reader_page = QWidget()
        self.init_news_reader_page()
        self.stacked_widget.addWidget(self.news_reader_page)  # index 5

        # ── Page 6: Instances (wizard-style) ──
        self.instances_page = QWidget()
        self.init_instances_page()
        self.stacked_widget.addWidget(self.instances_page)  # index 6

        right_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(right_area)
 
        # ── Resize grip (bottom-right of whole window) ──
        # ── Невидимі маркери зміни розміру (всі краї/кути КРІМ правого верхнього) ──
        T = 8  # товщина зони захоплення
        self._resize_grips = {
            'bottom':       ResizeGrip(self, 'bottom',       T),
            'right':        ResizeGrip(self, 'right',        T),
            'left':         ResizeGrip(self, 'left',         T),
            'bottom-right': ResizeGrip(self, 'bottom-right', T * 2),
            'bottom-left':  ResizeGrip(self, 'bottom-left',  T * 2),
            'top-left':     ResizeGrip(self, 'top-left',     T * 2),
        }
        for g in self._resize_grips.values():
            g.raise_()
 
        self._populate_version_combo()
 
    # ── FULL SCREEN SPECS PAGE ──
    def init_specs_page(self):
        layout = QVBoxLayout(self.specs_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background:#1a1a1a; border-bottom:1px solid #333;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(
            getattr(self, "_specs_prev_page", 2)))
        title_lbl = QLabel("Характеристики пристрою")
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_lbl.setStyleSheet("color: #4caf50; background: transparent;")
        hdr_lay.addWidget(btn_back)
        hdr_lay.addSpacing(16)
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()
        layout.addWidget(hdr)
        # Placeholder — content loaded async on first open
        self._specs_scroll = QScrollArea()
        self._specs_scroll.setWidgetResizable(True)
        self._specs_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        placeholder = QWidget()
        placeholder.setStyleSheet("background: transparent;")
        ph_lay = QVBoxLayout(placeholder)
        loading_lbl = QLabel("⏳ Завантаження характеристик...")
        loading_lbl.setAlignment(Qt.AlignCenter)
        loading_lbl.setStyleSheet("color:#888; font-size:14px; background:transparent;")
        ph_lay.addStretch()
        ph_lay.addWidget(loading_lbl)
        ph_lay.addStretch()
        self._specs_scroll.setWidget(placeholder)
        layout.addWidget(self._specs_scroll)
        self._specs_loaded = False
        self._specs_prev_page = 2

    def _update_specs_page(self):
        """Called on first open of specs page — gathers data async (no freeze)."""
        if getattr(self, "_specs_loaded", False):
            return
        self._specs_loaded = True

        def _gather():
            import multiprocessing, socket as _sock
            cards = []
            try:
                cpu_name = platform.processor() or platform.machine() or "N/A"
                try:
                    freq = psutil.cpu_freq()
                    freq_s = f" @ {freq.max/1000:.1f} GHz" if freq else ""
                except: freq_s = ""
                cores = multiprocessing.cpu_count()
                cards.append(("🖥", "ПРОЦЕСОР", f"{cpu_name}{freq_s}\n{cores} ядер/потоків", "#4fc3f7"))
            except: cards.append(("🖥", "ПРОЦЕСОР", "N/A", "#4fc3f7"))
            try:
                if psutil:
                    vm = psutil.virtual_memory()
                    ram = f"{vm.total/1024**3:.1f} ГБ  ({vm.percent:.0f}% використано)"
                    sw = psutil.swap_memory()
                    if sw.total > 0: ram += f"\nПідкачка: {sw.total/1024**3:.1f} ГБ"
                    cards.append(("💾", "ОЗУ", ram, "#81c784"))
                else: cards.append(("💾", "ОЗУ", "N/A", "#81c784"))
            except: cards.append(("💾", "ОЗУ", "N/A", "#81c784"))
            gpu_str = "N/A"
            try:
                r3 = _run_hidden(["wmic","path","win32_VideoController","get","Name"],
                                 capture_output=True, text=True, timeout=3)
                gl2 = [l.strip() for l in r3.stdout.splitlines() if l.strip() and l.strip()!="Name"]
                if gl2: gpu_str = "\n".join(gl2)
            except: pass
            if gpu_str == "N/A":
                try:
                    rp2 = _run_hidden(["powershell","-NoProfile","-Command",
                        "(Get-WmiObject Win32_VideoController|Select-Object -ExpandProperty Name)-join '\\n'"],
                        capture_output=True, text=True, timeout=4)
                    if rp2.stdout.strip(): gpu_str = rp2.stdout.strip()
                except: pass
            cards.append(("🎮", "ВІДЕОКАРТА", gpu_str, "#ce93d8"))
            try:
                disk = psutil.disk_usage(CONFIG_DIR)
                disk_str = f"{disk.free/1024**3:.1f} ГБ вільно / {disk.total/1024**3:.0f} ГБ"
            except: disk_str = "N/A"
            cards.append(("💿", "ДИСК", disk_str, "#ffb74d"))
            os_str = f"{platform.system()} {platform.release()} ({platform.machine()})"
            cards.append(("🪟", "ОПЕРАЦІЙНА СИСТЕМА", os_str, "#4dd0e1"))
            java_str = "не знайдено"
            try:
                jr2 = _run_hidden(["java","-version"], capture_output=True, text=True, timeout=3)
                jl2 = (jr2.stderr or jr2.stdout).splitlines()
                if jl2: java_str = jl2[0]
            except: pass
            cards.append(("☕", "JAVA", java_str, "#ff8a65"))
            cards.append(("🐍", "PYTHON", platform.python_version(), "#fff176"))
            try: host = _sock.gethostname()
            except: host = "N/A"
            cards.append(("🖥", "КОМП'ЮТЕР", host, "#90a4ae"))
            return cards

        def _on_done(cards_data):
            def _mat_card(icon, title, value, color):
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2a2a2a,stop:1 #222);
                        border: none;
                        border-radius: 10px;
                    }}
                """)
                # Окрема вузька кольорова смужка зліва (без border-radius, щоб не виглядала як дужка)
                outer = QHBoxLayout(card)
                outer.setContentsMargins(0, 0, 0, 0)
                outer.setSpacing(0)
                stripe = QFrame()
                stripe.setFixedWidth(4)
                stripe.setStyleSheet(f"background:{color}; border:none; border-radius:0;")
                outer.addWidget(stripe)

                inner = QWidget()
                inner.setStyleSheet("background: transparent; border: none;")
                cl = QVBoxLayout(inner)
                cl.setContentsMargins(14, 12, 14, 12)
                cl.setSpacing(4)
                top = QHBoxLayout()
                ic = QLabel(icon)
                ic.setStyleSheet(f"color:{color};font-size:20px;background:transparent;border:none;")
                tl = QLabel(title)
                tl.setStyleSheet("color:#888;font-size:11px;background:transparent;border:none;letter-spacing:1px;")
                top.addWidget(ic); top.addWidget(tl); top.addStretch()
                vl = QLabel(value); vl.setWordWrap(True)
                vl.setStyleSheet(f"color:#eee;font-size:13px;font-weight:bold;background:transparent;border:none;")
                cl.addLayout(top); cl.addWidget(vl)
                outer.addWidget(inner)
                return card
            content = QWidget(); content.setStyleSheet("background: transparent;")
            c_layout = QVBoxLayout(content)
            c_layout.setContentsMargins(40,30,40,30); c_layout.setSpacing(20)
            specs_grid = QGridLayout(); specs_grid.setSpacing(12)
            for i, (ic, ttl, val, clr) in enumerate(cards_data):
                specs_grid.addWidget(_mat_card(ic, ttl, val, clr), i//2, i%2)
            c_layout.addLayout(specs_grid); c_layout.addStretch()
            self._specs_scroll.setWidget(content)

        class _SpecsThread(QThread):
            done = pyqtSignal(object)
            def run(self):
                try: self.done.emit(_gather())
                except Exception as e: self.done.emit([("⚠", "ERROR", str(e), "#ef5350")])
        self._specs_thread = _SpecsThread()
        self._specs_thread.done.connect(_on_done)
        self._specs_thread.start()


    # ── VERSION COMBO ──
    INSTANCE_PREFIX = "📦 "  # Префікс для власних збірок у списку версій

    def _populate_version_combo(self):
        downloaded = get_downloaded_versions()
        self.version_combo.blockSignals(True)
        self.version_combo.clear()

        # Спочатку власні збірки користувача (як у PojavLauncher/FCL)
        instances = load_instances()
        for inst in instances:
            label = f"{self.INSTANCE_PREFIX}{inst['name']}"
            self.version_combo.addItem(label)
            idx = self.version_combo.count() - 1
            self.version_combo.setItemData(idx, inst, Qt.UserRole)

        if instances:
            self.version_combo.insertSeparator(self.version_combo.count())

        show_snaps = getattr(self, "_show_snapshots", True)
        versions_to_show = (SNAPSHOTS if show_snaps else []) + ALL_VERSIONS
        for v in versions_to_show:
            mc_ver, _ = get_mc_ver_and_loader(v)
            is_dl = mc_ver in downloaded
            prefix = "✔ " if is_dl else "   "
            self.version_combo.addItem(prefix + v)
        self.version_combo.blockSignals(False)
        self._on_version_changed(self.version_combo.currentIndex())

    def refresh_version_combo(self):
        current = self._current_version_text()
        self._populate_version_combo()
        for i in range(self.version_combo.count()):
            txt = self.version_combo.itemText(i)
            if txt.strip().lstrip("✔").strip() == current or txt == current:
                self.version_combo.setCurrentIndex(i)
                break

    def _current_version_text(self):
        t = self.version_combo.currentText()
        if t.startswith(self.INSTANCE_PREFIX):
            return t
        return t.strip().lstrip("✔").strip()

    def _current_instance_data(self):
        """Якщо обрано власну збірку — повертає її dict, інакше None."""
        idx = self.version_combo.currentIndex()
        data = self.version_combo.itemData(idx, Qt.UserRole)
        return data if isinstance(data, dict) else None

    def _on_version_changed(self, idx):
        inst = self._current_instance_data()
        if hasattr(self, "btn_manage_instance"):
            self.btn_manage_instance.setVisible(inst is not None)

    # ── СТОРІНКА ЗБІРОК (INSTANCES) — повноекранна, поетапна, з кнопкою "Назад" ──
    def init_instances_page(self):
        """
        Повноекранна сторінка управління збірками (як окрема вкладка бічної панелі).
        Має внутрішній QStackedWidget з двома "видами":
          0) Список усіх збірок + кнопка "Створити нову"
          1) Поетапний майстер створення (назва → версія → лоадер → готово)
        Перехід між ними — як вкладки, без модальних діалогів.
        """
        layout = QVBoxLayout(self.instances_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background:#1a1a1a; border-bottom:1px solid #333;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)
        btn_back = QPushButton("← Назад")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self._instances_title_lbl = QLabel("Збірки")
        self._instances_title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._instances_title_lbl.setStyleSheet("color: #4caf50; background: transparent;")
        hdr_lay.addWidget(btn_back)
        hdr_lay.addSpacing(16)
        hdr_lay.addWidget(self._instances_title_lbl)
        hdr_lay.addStretch()
        layout.addWidget(hdr)

        # Внутрішній перемикач "список" / "майстер"
        self._instances_stack = QStackedWidget()
        layout.addWidget(self._instances_stack, 1)

        self._build_instances_list_view()
        self._build_instance_wizard_view()

        self._instances_stack.setCurrentIndex(0)

    # ── Вид 0: список збірок ──
    def _build_instances_list_view(self):
        page = QWidget()
        page.setStyleSheet("background:#1a1a1a;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(30, 24, 30, 24)
        outer.setSpacing(16)

        top_row = QHBoxLayout()
        intro = QLabel(
            "Кожна збірка має свою власну папку для модів, сейвів і конфігів — "
            "так само як у PojavLauncher / FCL."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#888; font-size:12px; background:transparent;")
        top_row.addWidget(intro, 1)
        btn_new = QPushButton("➕  Створити нову збірку")
        btn_new.setStyleSheet(
            "QPushButton { background:#2e7d32; color:white; border-radius:8px; padding:10px 18px; font-weight:bold; }"
            "QPushButton:hover { background:#388e3c; }"
        )
        btn_new.clicked.connect(self._show_instance_wizard)
        top_row.addWidget(btn_new)
        outer.addLayout(top_row)

        self.instances_list_widget = QListWidget()
        self.instances_list_widget.setStyleSheet(
            "QListWidget { background:#222; border:1px solid #3a3a3a; border-radius:10px; "
            "color:#ddd; padding:4px; }"
            "QListWidget::item { padding: 10px; border-radius:6px; }"
            "QListWidget::item:selected { background:#2e7d32; }"
            "QListWidget::item:hover:!selected { background:#2a2a2a; }"
        )
        outer.addWidget(self.instances_list_widget, 1)
        self._refresh_instances_list_widget()

        btn_row = QHBoxLayout()
        btn_inst_mods = QPushButton("📁 Моди обраної")
        btn_inst_mods.setStyleSheet("background:#1565c0; color:white; padding:8px 16px; border-radius:8px;")
        btn_inst_mods.clicked.connect(self._manage_selected_instance_mods)
        btn_inst_folder = QPushButton("📂 Відкрити папку")
        btn_inst_folder.setStyleSheet("background:#444; color:#ccc; padding:8px 16px; border-radius:8px;")
        btn_inst_folder.clicked.connect(self._open_selected_instance_folder)
        btn_inst_delete = QPushButton("🗑 Видалити")
        btn_inst_delete.setStyleSheet("background:#b71c1c; color:white; padding:8px 16px; border-radius:8px;")
        btn_inst_delete.clicked.connect(self._delete_selected_instance_from_tab)
        btn_row.addWidget(btn_inst_mods)
        btn_row.addWidget(btn_inst_folder)
        btn_row.addStretch()
        btn_row.addWidget(btn_inst_delete)
        outer.addLayout(btn_row)

        self._instances_stack.addWidget(page)

    # ── Вид 1: поетапний майстер створення (як було у вікні, тільки тепер вкладка) ──
    def _build_instance_wizard_view(self):
        page = QWidget()
        page.setStyleSheet("background:#1a1a1a;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(40, 30, 40, 30)
        outer.setSpacing(18)

        self._wiz_step_lbl = QLabel("Крок 1 з 4 — Назва збірки")
        self._wiz_step_lbl.setStyleSheet("color:#80deea; font-size:12px; font-weight:bold; background:transparent;")
        outer.addWidget(self._wiz_step_lbl)

        self._wiz_stack = QStackedWidget()
        outer.addWidget(self._wiz_stack, 1)

        self._wiz_step = 0
        self._build_wiz_step_name()
        self._build_wiz_step_version()
        self._build_wiz_step_loader()
        self._build_wiz_step_summary()

        nav_row = QHBoxLayout()
        self._wiz_btn_back = QPushButton("← Назад")
        self._wiz_btn_back.setStyleSheet("background:#444; color:white; border-radius:8px; padding:9px 18px;")
        self._wiz_btn_back.clicked.connect(self._wiz_go_back)
        self._wiz_btn_back.setEnabled(False)

        btn_cancel_wiz = QPushButton("Скасувати")
        btn_cancel_wiz.setStyleSheet("background:#444; color:#ccc; border-radius:8px; padding:9px 18px;")
        btn_cancel_wiz.clicked.connect(self._cancel_instance_wizard)

        self._wiz_btn_next = QPushButton("Далі →")
        self._wiz_btn_next.setStyleSheet(
            "QPushButton { background:#2e7d32; color:white; border-radius:8px; padding:9px 18px; font-weight:bold; }"
            "QPushButton:hover { background:#388e3c; }"
        )
        self._wiz_btn_next.clicked.connect(self._wiz_go_next)

        nav_row.addWidget(self._wiz_btn_back)
        nav_row.addWidget(btn_cancel_wiz)
        nav_row.addStretch()
        nav_row.addWidget(self._wiz_btn_next)
        outer.addLayout(nav_row)

        self._instances_stack.addWidget(page)

    def _build_wiz_step_name(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)
        lbl = QLabel("Як назвемо цю збірку?")
        lbl.setStyleSheet("font-size:16px; font-weight:bold; background:transparent;")
        lay.addWidget(lbl)
        hint = QLabel("Наприклад: \"Better Than Wolves\", \"Технічний 1.20\", \"Виживання з друзями\"")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:12px; background:transparent;")
        lay.addWidget(hint)
        self.wiz_name_input = QLineEdit()
        self.wiz_name_input.setPlaceholderText("Назва збірки...")
        self.wiz_name_input.setMinimumHeight(38)
        self.wiz_name_input.setStyleSheet(
            "background:#2a2a2a; color:#eee; border:1px solid #444; border-radius:6px; padding:8px;")
        lay.addWidget(self.wiz_name_input)
        lay.addStretch()
        self._wiz_stack.addWidget(page)

    def _build_wiz_step_version(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)
        lbl = QLabel("Яку версію Minecraft використовувати?")
        lbl.setStyleSheet("font-size:16px; font-weight:bold; background:transparent;")
        lay.addWidget(lbl)
        self.wiz_version_combo = NoScrollCombo()
        self.wiz_version_combo.setEditable(True)
        self.wiz_version_combo.setMinimumHeight(38)
        seen_v = set()
        for v in ALL_VERSIONS:
            mc_ver_v, _ = get_mc_ver_and_loader(v)
            if mc_ver_v not in seen_v:
                seen_v.add(mc_ver_v)
                self.wiz_version_combo.addItem(mc_ver_v)
        lay.addWidget(self.wiz_version_combo)
        lay.addStretch()
        self._wiz_stack.addWidget(page)

    def _build_wiz_step_loader(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)
        lbl = QLabel("Мод-лоадер")
        lbl.setStyleSheet("font-size:16px; font-weight:bold; background:transparent;")
        lay.addWidget(lbl)
        hint = QLabel("Якщо плануєш встановлювати моди — обери відповідний лоадер.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:12px; background:transparent;")
        lay.addWidget(hint)
        self.wiz_loader_combo = NoScrollCombo()
        self.wiz_loader_combo.setMinimumHeight(38)
        self.wiz_loader_combo.addItems(["Vanilla (без модів)", "Forge", "Fabric", "NeoForge"])
        lay.addWidget(self.wiz_loader_combo)
        lay.addStretch()
        self._wiz_stack.addWidget(page)

    def _build_wiz_step_summary(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)
        lbl = QLabel("Все готово!")
        lbl.setStyleSheet("font-size:16px; font-weight:bold; background:transparent;")
        lay.addWidget(lbl)
        hint = QLabel("RAM та аргументи JVM використовуються загальні з налаштувань лаунчера.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:12px; background:transparent;")
        lay.addWidget(hint)
        self.wiz_summary_lbl = QLabel("")
        self.wiz_summary_lbl.setWordWrap(True)
        self.wiz_summary_lbl.setStyleSheet(
            "color:#80deea; font-size:13px; background:#1a2a2e; border-radius:8px; padding:14px; margin-top:8px;")
        lay.addWidget(self.wiz_summary_lbl)
        lay.addStretch()
        self._wiz_stack.addWidget(page)

    def _update_wiz_summary(self):
        name = self.wiz_name_input.text().strip() or "(без назви)"
        ver = self.wiz_version_combo.currentText().strip()
        loader = self.wiz_loader_combo.currentText().split(" ")[0]
        self.wiz_summary_lbl.setText(f"📦 «{name}»  —  Minecraft {ver}  —  {loader}")

    def _show_instance_wizard(self):
        """Перемикає внутрішній стек на вид майстра і скидає його на крок 1."""
        self.wiz_name_input.clear()
        self._wiz_step = 0
        self._wiz_stack.setCurrentIndex(0)
        self._wiz_btn_back.setEnabled(False)
        self._wiz_btn_next.setText("Далі →")
        self._wiz_step_lbl.setText("Крок 1 з 4 — Назва збірки")
        self._instances_stack.setCurrentIndex(1)

    def _cancel_instance_wizard(self):
        self._instances_stack.setCurrentIndex(0)

    def _wiz_go_next(self):
        labels = ["Назва збірки", "Версія Minecraft", "Мод-лоадер", "Готово"]
        if self._wiz_step == 0:
            name = self.wiz_name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Помилка", "Введіть назву збірки.")
                return
            if get_instance_by_name(name):
                QMessageBox.warning(self, "Помилка", "Збірка з такою назвою вже існує.")
                return
        if self._wiz_step == 3:
            self._finish_instance_wizard()
            return
        if self._wiz_step == 2:
            self._update_wiz_summary()
        self._wiz_step += 1
        self._wiz_stack.setCurrentIndex(self._wiz_step)
        self._wiz_btn_back.setEnabled(True)
        self._wiz_step_lbl.setText(f"Крок {self._wiz_step + 1} з 4 — {labels[self._wiz_step]}")
        if self._wiz_step == 3:
            self._wiz_btn_next.setText("✓ Створити")
            self._update_wiz_summary()

    def _wiz_go_back(self):
        if self._wiz_step == 0:
            return
        labels = ["Назва збірки", "Версія Minecraft", "Мод-лоадер", "Готово"]
        self._wiz_step -= 1
        self._wiz_stack.setCurrentIndex(self._wiz_step)
        self._wiz_btn_back.setEnabled(self._wiz_step > 0)
        self._wiz_step_lbl.setText(f"Крок {self._wiz_step + 1} з 4 — {labels[self._wiz_step]}")
        self._wiz_btn_next.setText("Далі →" if self._wiz_step < 3 else "✓ Створити")

    def _finish_instance_wizard(self):
        name = self.wiz_name_input.text().strip()
        mc_version = self.wiz_version_combo.currentText().strip()
        if not mc_version:
            QMessageBox.warning(self, "Помилка", "Оберіть версію Minecraft.")
            return
        loader_map = {"Vanilla": "vanilla", "Forge": "forge", "Fabric": "fabric", "NeoForge": "neoforge"}
        loader_key = self.wiz_loader_combo.currentText().split(" ")[0]
        loader = loader_map.get(loader_key, "vanilla")

        ok, result = add_instance(name, mc_version, loader)
        if not ok:
            QMessageBox.warning(self, "Помилка", result)
            return

        self._refresh_instances_list_widget()
        self.refresh_version_combo()
        label = f"{self.INSTANCE_PREFIX}{name}"
        idx = self.version_combo.findText(label)
        if idx >= 0:
            self.version_combo.setCurrentIndex(idx)

        self._instances_stack.setCurrentIndex(0)
        QMessageBox.information(
            self, "Готово", f"Збірка «{name}» створена!\nТепер можна додати моди зі списку.")

    # ── Допоміжні методи списку збірок ──
    def _refresh_instances_list_widget(self):
        if not hasattr(self, "instances_list_widget"):
            return
        self.instances_list_widget.clear()
        instances = load_instances()
        if not instances:
            self.instances_list_widget.addItem("(збірок ще немає — натисніть \"Створити нову збірку\")")
            return
        for inst in instances:
            loader_name = (inst.get("loader") or "vanilla").capitalize()
            item = QListWidgetItem(f"📦 {inst['name']}  —  MC {inst['mc_version']}  —  {loader_name}")
            item.setData(Qt.UserRole, inst)
            self.instances_list_widget.addItem(item)

    def _get_selected_instance_from_tab(self):
        item = self.instances_list_widget.currentItem()
        if not item:
            return None
        data = item.data(Qt.UserRole)
        return data if isinstance(data, dict) else None

    def _manage_selected_instance_mods(self):
        inst = self._get_selected_instance_from_tab()
        if not inst:
            QMessageBox.information(self, "Інфо", "Спочатку оберіть збірку зі списку.")
            return
        dlg = InstanceModsDialog(self, inst)
        dlg.exec_()

    def _open_selected_instance_folder(self):
        inst = self._get_selected_instance_from_tab()
        if not inst:
            QMessageBox.information(self, "Інфо", "Спочатку оберіть збірку зі списку.")
            return
        inst_dir = get_instance_dir(inst["name"])
        os.makedirs(inst_dir, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(inst_dir)
        except Exception:
            pass

    def _delete_selected_instance_from_tab(self):
        inst = self._get_selected_instance_from_tab()
        if not inst:
            QMessageBox.information(self, "Інфо", "Спочатку оберіть збірку зі списку.")
            return
        confirmed = CountdownConfirmDialog.ask(
            self, "Видалення збірки",
            f"Збірку «{inst['name']}» та ВСІ її дані (моди, сейви, конфіги) "
            f"буде видалено НАЗАВЖДИ. Цю дію неможливо відмінити.",
            confirm_text="Видалити назавжди", seconds=10, danger=True)
        if not confirmed:
            return
        delete_instance(inst["name"], delete_files=True)
        self._refresh_instances_list_widget()
        self.refresh_version_combo()
        self.version_combo.setCurrentIndex(0)

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

        # ── Список встановлених версій Java ──
        java_list_box = QGroupBox("ВСТАНОВЛЕНІ ВЕРСІЇ JAVA")
        java_list_box.setStyleSheet(GRP)
        java_list_vbox = QVBoxLayout(java_list_box)

        jl_desc = QLabel(
            "Системні Java та Mojang-runtime, завантажені лаунчером автоматично "
            "для запуску різних версій Minecraft."
        )
        jl_desc.setWordWrap(True)
        jl_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        java_list_vbox.addWidget(jl_desc)

        self.java_list_widget = QListWidget()
        self.java_list_widget.setMaximumHeight(160)
        self.java_list_widget.setStyleSheet(
            "QListWidget { background:#1e1e1e; border:1px solid #444; border-radius:6px; color:#ddd; }"
            "QListWidget::item { padding: 5px 8px; }"
        )
        java_list_vbox.addWidget(self.java_list_widget)

        jl_btn_row = QHBoxLayout()
        btn_java_rescan = QPushButton("🔄 Оновити список")
        btn_java_rescan.setStyleSheet("background:#1565c0; color:white; padding:6px 12px; border-radius:6px;")
        btn_java_rescan.clicked.connect(self._refresh_java_list)
        btn_java_use_selected = QPushButton("✔ Використати обрану")
        btn_java_use_selected.setStyleSheet("background:#2e7d32; color:white; padding:6px 12px; border-radius:6px;")
        btn_java_use_selected.clicked.connect(self._use_selected_java)
        jl_btn_row.addWidget(btn_java_rescan)
        jl_btn_row.addWidget(btn_java_use_selected)
        java_list_vbox.addLayout(jl_btn_row)

        lay_java.addWidget(java_list_box)
        # НЕ запускаємо авто-сканування при старті лаунчера — воно займає 3-4 сек
        # і показує консольне вікно (java -version). Список заповниться тільки
        # коли користувач сам натисне "Оновити список" у вкладці Java.

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
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти"])
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
        self.ui_style_combo.addItems(["G9 UI", "MetroUI", "Round UI"])
        self.ui_style_combo.setFixedWidth(200)
        def on_ui_style(s):
            self._ui_style = s
            self._apply_ui_style()
            self.save_settings()
        self.ui_style_combo.currentTextChanged.connect(on_ui_style)
        style_row.addWidget(self.ui_style_combo)
        style_vbox.addLayout(style_row)
        lay_custom.addWidget(style_box)

        # ─ Скидання (3 окремі кнопки з підтвердженням і таймером) ─
        reset_all_box = QGroupBox("СКИДАННЯ")
        reset_all_box.setStyleSheet(GRP)
        reset_all_vbox = QVBoxLayout(reset_all_box)
        reset_desc = QLabel(
            "Кожна дія потребує підтвердження з таймером 10с, щоб уберегти "
            "від випадкового натискання."
        )
        reset_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        reset_desc.setWordWrap(True)
        reset_all_vbox.addWidget(reset_desc)

        # 1) Скинути Minecraft (видаляє ігрові файли: версії, моди, сейви, інстанси)
        btn_reset_mc = QPushButton("🎮  Скинути Minecraft (видалити всі версії, моди, сейви)")
        btn_reset_mc.setStyleSheet(
            "background: #e65100; color: white; border: 2px solid #bf360c; "
            "padding: 8px; border-radius: 6px; font-weight: bold;"
        )
        btn_reset_mc.clicked.connect(self._confirm_reset_minecraft)
        reset_all_vbox.addWidget(btn_reset_mc)

        # 2) Скинути лаунчер (тільки налаштування інтерфейсу/конфіг)
        btn_reset_launcher = QPushButton("⚙  Скинути лаунчер (налаштування та вигляд)")
        btn_reset_launcher.setStyleSheet(
            "background: #1565c0; color: white; border: 2px solid #0d47a1; "
            "padding: 8px; border-radius: 6px; font-weight: bold;"
        )
        btn_reset_launcher.clicked.connect(self._confirm_reset_all)
        reset_all_vbox.addWidget(btn_reset_launcher)

        # 3) Скинути все разом
        btn_reset_everything = QPushButton("🗑  Скинути ВСЕ (Minecraft + лаунчер)")
        btn_reset_everything.setStyleSheet(
            "background: #c62828; color: white; border: 2px solid #b71c1c; "
            "padding: 8px; border-radius: 6px; font-weight: bold;"
        )
        btn_reset_everything.clicked.connect(self._confirm_reset_everything)
        reset_all_vbox.addWidget(btn_reset_everything)

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

        # ─ Ізоляція версій (як у Prism Launcher) ─
        isolate_box = QGroupBox("ІЗОЛЯСІЯ ВЕРСІЙ")
        isolate_box.setStyleSheet(GRP)
        isolate_vbox = QVBoxLayout(isolate_box)

        isolate_desc = QLabel(
            "Кожна версія/збірка отримує свою власну папку для mods, saves "
            "і config — щоб вони не змішувались між різними версіями та модлоадерами."
        )
        isolate_desc.setWordWrap(True)
        isolate_desc.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        isolate_vbox.addWidget(isolate_desc)

        row_isolate = QHBoxLayout()
        row_isolate.addWidget(QLabel("Ізолювати моди/сейви по версіях"))
        row_isolate.addStretch()
        self.chk_isolate_versions = ToggleSwitch(checked=True)
        def toggle_isolate(val):
            self._isolate_versions = val
            self.save_settings()
        self.chk_isolate_versions.toggled.connect(toggle_isolate)
        row_isolate.addWidget(self.chk_isolate_versions)
        isolate_vbox.addLayout(row_isolate)

        isolate_warn = QLabel(
            "⚠ Зміна цієї опції не переносить уже існуючі сейви — "
            "вони залишаться у старій папці."
        )
        isolate_warn.setWordWrap(True)
        isolate_warn.setStyleSheet("color: #ffb74d; font-size:10px; background:transparent;")
        isolate_vbox.addWidget(isolate_warn)

        lay_beh.addWidget(isolate_box)

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
 
        info_vbox.addLayout(_info_row2("Версія лаунчера:", "1.5 FP 1"))

        dev_row = QHBoxLayout()
        dev_key = QLabel("Розробник:")
        dev_key.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        dev_val = QLabel(
            "<span style='color:#4caf50; font-weight:bold;'>G9 Studio</span>"
            "<span style='color:#888;'> + </span>"
            "<span style='color:#4da6ff; font-weight:bold;'>ALFA Studios</span>"
        )
        dev_val.setStyleSheet("font-size: 12px; background: transparent;")
        dev_row.addWidget(dev_key)
        dev_row.addStretch()
        dev_row.addWidget(dev_val)
        info_vbox.addLayout(dev_row)
 
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #3a3a3a;")
        info_vbox.addWidget(sep2)
 
        # Button to full specs page
        btn_specs_full = QPushButton("📊 Характеристики пристрою →")
        btn_specs_full.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 10px 16px;
                background: #1e2a1e; color: #9ccc65;
                border: 1px solid #4caf50; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #2a3a2a; }
        """)
        btn_specs_full.clicked.connect(lambda: self.switch_page(4))
        info_vbox.addWidget(btn_specs_full)

        # Update check button — без рамки (тільки текст)
        upd_widget = QWidget()
        upd_widget.setStyleSheet("background: transparent;")
        upd_layout = QHBoxLayout(upd_widget)
        upd_layout.setContentsMargins(0, 8, 0, 8)
        
        upd_icon = QLabel("🔄")
        upd_icon.setStyleSheet("font-size:18px; background:transparent;")
        
        self._upd_status_lbl = QLabel(f"Поточна версія: {_LAUNCHER_VERSION}")
        self._upd_status_lbl.setStyleSheet("color: #90caf9; font-size:12px; background:transparent;")
        
        self._upd_check_btn = QPushButton("Перевірити")
        self._upd_check_btn.setStyleSheet("""
            QPushButton {
                background: #1565c0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #1976d2; }
            QPushButton:disabled { background: #555; color: #999; }
        """)
        self._upd_check_btn.clicked.connect(lambda: self.check_for_update_now(silent=False))
        
        upd_layout.addWidget(upd_icon)
        upd_layout.addWidget(self._upd_status_lbl)
        upd_layout.addStretch()
        upd_layout.addWidget(self._upd_check_btn)
        info_vbox.addWidget(upd_widget)
 
        lay_about.addWidget(info_box)
        lay_about.addStretch()
        self._settings_tabs.addTab(tab_about, "ℹ  Про програму")
 
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
 
        c_layout.addWidget(info_card("Версія лаунчера", "1.5 FP 1", "#4caf50"))
        c_layout.addWidget(info_card("Розробник", "G9 Studio + ALFA Studios", "#4caf50"))
 
        # ── Button to full specs page ──
        btn_specs_full = QPushButton("📊 Характеристики пристрою →")
        btn_specs_full.setStyleSheet("""
            QPushButton {
                text-align: center; padding: 12px;
                background: #1e2a1e; color: #9ccc65;
                border: 1px solid #4caf50; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #2a3a2a; }
        """)
        btn_specs_full.clicked.connect(lambda: self.switch_page(4))
        c_layout.addWidget(btn_specs_full)
 
        c_layout.addStretch()
 
        btns_row = QHBoxLayout()
        btn_site = QPushButton("🌐 Сайт проекту")
        btn_site.setToolTip("Відкрити сайт проекту")
        btn_site.clicked.connect(lambda: self._open_url("https://devalfastudios.github.io/G9-Launcher/"))
        self._about_upd_btn = QPushButton("🔄 Перевірити оновлення")
        self._about_upd_btn.setStyleSheet("background: #1565c0; color: white; padding: 6px 14px; border-radius: 6px; font-weight: bold;")
        self._about_upd_btn.clicked.connect(lambda: self.check_for_update_now(silent=False))
        btn_back = QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btns_row.addWidget(btn_back)
        btns_row.addStretch()
        btns_row.addWidget(self._about_upd_btn)
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

        btn_skin_upload = QPushButton("📂 Завантажити скін")
        btn_skin_upload.setToolTip("Обрати PNG-файл скіна (64x64) для поточного ніка")
        btn_skin_upload.setStyleSheet(
            "background:#1565c0; color:white; padding:5px 10px; border-radius:5px; font-size:11px;")
        btn_skin_upload.clicked.connect(self._upload_local_skin)

        btn_skin_remove = QPushButton("✕ Видалити локальний")
        btn_skin_remove.setToolTip("Видалити локальний скін, повернутись до minotar.net")
        btn_skin_remove.setStyleSheet(
            "background:#444; color:#ccc; padding:5px 10px; border-radius:5px; font-size:11px;")
        btn_skin_remove.clicked.connect(self._remove_local_skin_for_current)

        skin_row = QHBoxLayout()
        skin_col = QVBoxLayout()
        skin_col.addWidget(self.skin_viewer, 0, Qt.AlignCenter)
        skin_col.addWidget(self.skin_viewer_nick)
        skin_col.addWidget(btn_skin_upload)
        skin_col.addWidget(btn_skin_remove)
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
            self.skin_viewer.load_for_nick(nick)
            self.save_settings()
            self.stacked_widget.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Помилка", "Виберіть нік зі списку!")

    # ── LOCAL SKIN UPLOAD ──
    def _upload_local_skin(self):
        """Дозволяє обрати локальний PNG-файл скіна і прив'язати його до поточного ніка."""
        nick = self.nick_dialog.current_nick
        if not nick:
            QMessageBox.warning(self, "Помилка", "Спочатку оберіть або введіть нік.")
            return
        fname, _ = QFileDialog.getOpenFileName(
            self, f"Обрати скін для '{nick}'", "", "PNG зображення (*.png)")
        if not fname:
            return
        test_img = QImage(fname)
        if test_img.isNull():
            QMessageBox.warning(self, "Помилка", "Не вдалося прочитати зображення.")
            return
        w, h = test_img.width(), test_img.height()
        valid_sizes = {(64, 64), (64, 32)}
        if (w, h) not in valid_sizes:
            reply = QMessageBox.question(
                self, "Незвичний розмір",
                f"Обраний файл має розмір {w}x{h}, а стандартний скін Minecraft — "
                f"64x64 (новий формат) або 64x32 (старий).\n\n"
                f"Використати файл попри це?",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        dest = set_local_skin_path(nick, fname)
        if dest:
            self.skin_viewer.load_for_nick(nick)
            QMessageBox.information(
                self, "Готово", f"Локальний скін для '{nick}' встановлено.")
        else:
            QMessageBox.warning(self, "Помилка", "Не вдалося зберегти скін.")

    def _remove_local_skin_for_current(self):
        """Видаляє локальний скін поточного ніка, повертає онлайн-скін з minotar.net."""
        nick = self.nick_dialog.current_nick
        if not nick:
            return
        if remove_local_skin(nick):
            self.skin_viewer.load_for_nick(nick)
            QMessageBox.information(self, "Готово", f"Локальний скін для '{nick}' видалено.")
        else:
            QMessageBox.information(self, "Інфо", "Локального скіна для цього ніка не знайдено.")

 
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

        # Якщо обрано власну збірку — підставляємо її параметри замість стандартного рядка версії
        instance_data = self._current_instance_data()
        if instance_data:
            loader_name = (instance_data.get("loader") or "vanilla").capitalize()
            selected = f"{instance_data['mc_version']} - {loader_name}"
            self._active_instance_name = instance_data["name"]
        else:
            selected = self._current_version_text()
            self._active_instance_name = None

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
 
        def _set_status(txt):
            QTimer.singleShot(0, lambda: self.btn_play.setText(txt))

        def run():
            try:
                _set_status("Встановлення...")
                # Install the version; allow snapshots/pre-releases
                try:
                    minecraft_launcher_lib.install.install_minecraft_version(
                        mc_ver, CONFIG_DIR, allow_snapshots=True, allow_experimental=True)
                except TypeError:
                    minecraft_launcher_lib.install.install_minecraft_version(mc_ver, CONFIG_DIR)

                if loader == "forge":
                    _set_status("Встановлення Forge...")
                    try:
                        fv = minecraft_launcher_lib.forge.find_forge_version(mc_ver)
                        if fv and not minecraft_launcher_lib.forge.is_forge_version_valid(fv):
                            fv = None
                        if fv:
                            # supports_specific_version=False -> install_forge_version may need callback for old Forge installers (1.5-1.12) that download via a Java sub-process
                            try:
                                minecraft_launcher_lib.forge.install_forge_version(
                                    fv, CONFIG_DIR, callback={
                                        "setStatus": lambda t: _set_status(f"Forge: {t}"[:40])
                                    })
                            except TypeError:
                                minecraft_launcher_lib.forge.install_forge_version(fv, CONFIG_DIR)
                    except Exception as _fe:
                        print(f"Forge install warning: {_fe}")
                elif loader == "fabric":
                    _set_status("Встановлення Fabric...")
                    try:
                        minecraft_launcher_lib.fabric.install_fabric(mc_ver, CONFIG_DIR)
                    except Exception as _fae:
                        print(f"Fabric install warning: {_fae}")
                elif loader in ("neoforge", "quilt"):
                    _set_status(f"Встановлення {loader}...")
                    try:
                        ml = minecraft_launcher_lib.mod_loader.get_mod_loader(loader)
                        ml.install(mc_ver, CONFIG_DIR)
                    except Exception as _nfe:
                        print(f"{loader} install warning: {_nfe}")

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

                # ── Власна збірка (instance) має приоритет над загальною ізоляцією ──
                active_inst = getattr(self, "_active_instance_name", None)
                if active_inst:
                    mc_game_dir = get_instance_dir(active_inst)
                    os.makedirs(os.path.join(mc_game_dir, "mods"), exist_ok=True)
                    os.makedirs(os.path.join(mc_game_dir, "saves"), exist_ok=True)
                    os.makedirs(os.path.join(mc_game_dir, "config"), exist_ok=True)
                # ── Ізоляція версій (як у Prism Launcher) ──
                # Якщо увімкнено: кожна версія/збірка отримує свою власну
                # папку для mods/saves/config, щоб вони не змішувались
                # між різними версіями та модлоадерами.
                elif getattr(self, "_isolate_versions", True):
                    # Використовуємо ТІЛЬКИ версію MC (без лоадера) як назву папки —
                    # щоб сейви/конфіги були спільними між Vanilla/Forge однієї версії.
                    # Наприклад: "1.12.2 - Forge" → папка "1.12.2", не "1.12.2 - Forge"
                    safe_name = "".join(
                        c if c not in '<>:"/\\|?*' else "_" for c in mc_ver
                    ).strip()
                    mc_game_dir = os.path.join(CONFIG_DIR, "instances", safe_name)
                else:
                    mc_game_dir = os.path.join(CONFIG_DIR, "minecraft")
                os.makedirs(mc_game_dir, exist_ok=True)

                # ── Legacy audio fix (1.0 - 1.6.4): "глухі" старі версії ──
                # Копіюємо ресурси у CONFIG_DIR/assets/virtual/legacy/ —
                # це СПІЛЬНИЙ шлях для всіх версій/збірок, бо саме туди
                # дивиться сам клієнт через --assetsDir/${game_assets}
                # (підставляється minecraft_launcher_lib незалежно від
                # обраного gameDirectory). НЕ залежить від ізоляції версій.
                if _needs_legacy_audio_fix(mc_ver):
                    _set_status("Відновлення звуку...")
                    def _audio_progress(pct):
                        _set_status(f"Відновлення звуку... {pct}%")
                    try:
                        _fix_legacy_audio(mc_ver, CONFIG_DIR, progress_cb=_audio_progress)
                    except Exception as _ae:
                        print(f"Legacy audio fix warning: {_ae}")

                extra_jvm = []
                try:
                    if active_inst and instance_data and instance_data.get("jvm_args"):
                        raw = instance_data["jvm_args"].strip()
                    else:
                        raw = self.jvm_args_input.text().strip()
                    if raw:
                        extra_jvm = raw.split()
                except Exception:
                    pass

                # ── Автовибір Java під версію ──
                # Спочатку пробуємо встановити/знайти правильний Mojang JRE
                # для цієї конкретної версії (напр. Java 8 для 1.12.2, Java 17 для 1.18+,
                # Java 21+/25 для 26.x). Системна Java використовується тільки як fallback,
                # якщо пользувач вручну вказав свій шлях java.exe в налаштуваннях.
                custom_java = ""
                try:
                    lbl = getattr(self, "java_path_lbl", None)
                    if lbl:
                        p = lbl.text().strip()
                        if p and os.path.isfile(p):
                            custom_java = p
                except Exception:
                    pass

                fallback_java = _prefer_javaw(custom_java) if custom_java else ""
                if not fallback_java:
                    _set_status("Підбір Java...")
                    auto_java = _ensure_java_runtime(launch_id, CONFIG_DIR)
                    fallback_java = auto_java or _prefer_javaw(shutil.which("java")) or "java"

                _set_status("Завантаження...")

                ram_value = (instance_data.get("ram_gb", 2) if (active_inst and instance_data)
                             else self.ram_slider.value())

                # ── Розмір вікна гри ──
                # КРИТИЧНО для старих версій (LWJGL 2.x, до 1.12.2 включно):
                # без явного resolutionWidth/Height клієнт іноді створює
                # OpenGL-контекст з нульовим/некоректним розміром і вікно
                # просто не зʼявляється на екрані, хоча процес продовжує
                # працювати (звук, текстури завантажуються нормально).
                try:
                    win_width = int(self.win_w.text().strip()) if hasattr(self, "win_w") else 1280
                except Exception:
                    win_width = 1280
                try:
                    win_height = int(self.win_h.text().strip()) if hasattr(self, "win_h") else 720
                except Exception:
                    win_height = 720
                win_width = max(640, win_width)
                win_height = max(480, win_height)

                options = {
                    "username": nick,
                    "uuid": player_uuid,
                    "token": "0",
                    "defaultExecutablePath": fallback_java,
                    "gameDirectory": mc_game_dir,
                    "customResolution": True,
                    "resolutionWidth": str(win_width),
                    "resolutionHeight": str(win_height),
                    "jvmArguments": [
                        f"-Xmx{ram_value}G",
                        "-Xms512M",
                        "-XX:+UseG1GC",
                    ] + extra_jvm,
                    "launcherName": "G9Launcher",
                    "launcherVersion": "1.5-fp1",
                }
                cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_id, CONFIG_DIR, options)
                # Для старих версій (до 1.6.4) передаємо ресурси через -Dgameассети (старий клієнт шукає resources/ сам)
                # фільтруємо застарілі JVM аргументи несумісні з Java 21+/25
                _bad_args = {
                    "--sun-misc-unsafe-memory-access=allow",
                    "-XX:+UnlockExperimentalVMOptions",
                }
                cmd = [a for a in cmd if a not in _bad_args]
                # КРИТИЧНО: НЕ приховуємо вікно процесу через STARTUPINFO/SW_HIDE!
                # На старих версіях (LWJGL 2.x, до 1.12.2 включно) це призводить
                # до того, що ГОЛОВНЕ ВІКНО ГРИ створюється прихованим і ніколи
                # не зʼявляється на екрані — гра при цьому повністю працює
                # "невидимо" (звук, текстури завантажуються нормально), просто
                # вікно не показується. На новіших версіях/Forge це не
                # проявляється, бо вікно ініціалізується іншим механізмом.
                # CREATE_NO_WINDOW приховує чорне консольне вікно Java,
                # але НЕ впливає на головне вікно гри (на відміну від
                # STARTUPINFO/SW_HIDE, яке раніше ховало саму гру).
                # Якщо javaw.exe знайшли — він і так без консолі,
                # якщо java.exe — CREATE_NO_WINDOW прибирає консоль.
                launch_flags = 0
                if os.name == "nt":
                    launch_flags = subprocess.CREATE_NO_WINDOW
                self.minecraft_process = subprocess.Popen(
                    cmd, cwd=CONFIG_DIR,
                    creationflags=launch_flags
                )
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
            self.save_settings()

    def _refresh_java_list(self):
        """Сканує систему та Mojang runtime, заповнює список встановлених Java."""
        if not hasattr(self, "java_list_widget"):
            return
        self.java_list_widget.clear()
        loading_item = QListWidgetItem("🔄 Пошук встановлених Java...")
        self.java_list_widget.addItem(loading_item)

        def _worker():
            try:
                found = find_all_installed_java()
            except Exception as e:
                found = []
            QTimer.singleShot(0, lambda: _on_done(found))

        def _on_done(found):
            self.java_list_widget.clear()
            if not found:
                self.java_list_widget.addItem("❌ Жодної Java не знайдено")
                return
            for entry in found:
                item = QListWidgetItem(f"☕ {entry['version']}  —  {entry['source']}")
                item.setData(Qt.UserRole, entry["path"])
                item.setToolTip(entry["path"])
                self.java_list_widget.addItem(item)

        Thread(target=_worker, daemon=True).start()

    def _use_selected_java(self):
        """Застосовує обрану в списку Java як шлях за замовчуванням."""
        if not hasattr(self, "java_list_widget"):
            return
        item = self.java_list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Java", "Спочатку оберіть Java зі списку.")
            return
        path = item.data(Qt.UserRole)
        if not path:
            return
        if hasattr(self, "java_path_lbl"):
            self.java_path_lbl.setText(path)
        self.save_settings()
        QMessageBox.information(self, "Java", f"Обрано: {path}")

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
        if getattr(self, "_update_check_in_progress", False):
            return
        self._update_check_in_progress = True

        def _ui_checking():
            if hasattr(self, "_upd_status_lbl"):
                self._upd_status_lbl.setText("🔍 Перевірка оновлень...")
                self._upd_status_lbl.setStyleSheet("color:#ffb74d;font-size:12px;background:transparent;")
            for btn, txt in [(getattr(self, "_upd_check_btn", None), "Перевірка..."),
                             (getattr(self, "_about_upd_btn", None), "🔄 Перевірка...")]:
                if btn:
                    btn.setEnabled(False)
                    btn.setText(txt)

        if not silent:
            _ui_checking()

        def _ui_done(status_text, status_color):
            self._update_check_in_progress = False
            if hasattr(self, "_upd_status_lbl"):
                self._upd_status_lbl.setText(status_text)
                self._upd_status_lbl.setStyleSheet(f"color:{status_color};font-size:12px;background:transparent;")
            if hasattr(self, "_upd_check_btn"):
                self._upd_check_btn.setEnabled(True)
                self._upd_check_btn.setText("Перевірити")
            if hasattr(self, "_about_upd_btn"):
                self._about_upd_btn.setEnabled(True)
                self._about_upd_btn.setText("🔄 Перевірити оновлення")

        def _worker():
            info = _fetch_latest_release_info()

            if not info:
                QTimer.singleShot(0, lambda: _ui_done(
                    f"✅ Остання версія ({_LAUNCHER_VERSION})", "#81c784"))
                if not silent:
                    QTimer.singleShot(50, lambda: QMessageBox.information(
                        self, "Оновлення",
                        f"У вас вже встановлена остання версія: {_LAUNCHER_VERSION}\n\n"
                        f"(GitHub API не відповідає — перевірте підключення до інтернету.)"))
                return

            tag = info.get("tag_name", "")
            url = info.get("html_url", "")
            assets = info.get("assets", [])
            body = info.get("body", "")

            dl_url = ""
            for asset in assets:
                nm = asset.get("name", "").lower()
                if nm.endswith(".exe") or nm.endswith(".py"):
                    dl_url = asset.get("browser_download_url", "")
                    break

            if _is_newer_version(tag, _LAUNCHER_VERSION):
                QTimer.singleShot(0, lambda: _ui_done(f"⬆ Доступне оновлення: {tag}", "#ffb74d"))
                def _show():
                    notes = (body[:400] + "…") if len(body) > 400 else body
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
                QTimer.singleShot(50, _show)
            else:
                QTimer.singleShot(0, lambda: _ui_done(
                    f"✅ Остання версія ({_LAUNCHER_VERSION})", "#81c784"))
                if not silent:
                    QTimer.singleShot(50, lambda: QMessageBox.information(
                        self, "Оновлення",
                        f"У вас вже встановлена остання версія: {_LAUNCHER_VERSION}"))

        Thread(target=_worker, daemon=True).start()

    def _download_and_apply_update(self, dl_url, tag):
        """Завантажує файл оновлення і перезапускає лаунчер."""
        import tempfile
        # Show progress dialog
        prog = QProgressDialog(
            f"Завантаження оновлення {tag}...", "Скасувати", 0, 100, self)
        prog.setWindowTitle("Оновлення G9 Launcher")
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        prog.setValue(0)
        prog.show()
        cancelled = [False]
        prog.canceled.connect(lambda: cancelled.__setitem__(0, True))

        def _worker():
            try:
                ext = ".exe" if dl_url.lower().endswith(".exe") else ".py"
                current = os.path.abspath(sys.argv[0])
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
                os.close(tmp_fd)
                req = urllib.request.Request(dl_url, headers={"User-Agent": f"G9Launcher/{_LAUNCHER_VERSION}"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    total = int(r.headers.get("Content-Length", 0))
                    downloaded = 0
                    chunk = 8192
                    with open(tmp_path, "wb") as f:
                        while True:
                            if cancelled[0]:
                                os.remove(tmp_path)
                                QTimer.singleShot(0, prog.close)
                                return
                            data = r.read(chunk)
                            if not data:
                                break
                            f.write(data)
                            downloaded += len(data)
                            if total > 0:
                                pct = int(downloaded * 100 / total)
                                QTimer.singleShot(0, lambda p=pct: prog.setValue(p))
                QTimer.singleShot(0, lambda: prog.setValue(100))
                # Replace file
                backup = current + ".bak"
                try:
                    if os.path.exists(backup): os.remove(backup)
                    os.rename(current, backup)
                except Exception: pass
                import shutil as _sh
                _sh.copy2(tmp_path, current)
                os.remove(tmp_path)
                def _restart():
                    prog.close()
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
                QTimer.singleShot(0, prog.close)
                QTimer.singleShot(0, lambda: QMessageBox.critical(
                    self, "Помилка оновлення", f"Не вдалося завантажити оновлення:\n{e}"))
        Thread(target=_worker, daemon=True).start()

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
    def init_news_reader_page(self):
        """Page 5: full-screen news article reader with back button."""
        layout = QVBoxLayout(self.news_reader_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background:#1a1a1a; border-bottom:1px solid #333;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)
        self._news_back_btn = QPushButton("← Назад")
        self._news_back_btn.setFixedWidth(100)
        self._news_back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self._news_page_title = QLabel("Новина")
        self._news_page_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._news_page_title.setStyleSheet("color: #4caf50; background: transparent;")
        hdr_lay.addWidget(self._news_back_btn)
        hdr_lay.addSpacing(16)
        hdr_lay.addWidget(self._news_page_title)
        hdr_lay.addStretch()
        layout.addWidget(hdr)
        self._news_reader_scroll = QScrollArea()
        self._news_reader_scroll.setWidgetResizable(True)
        self._news_reader_scroll.setStyleSheet(
            "QScrollArea{border:none;background:#1a1a1a;}"
            "QScrollBar:vertical{background:#111;width:8px;border-radius:4px;}"
            "QScrollBar::handle:vertical{background:#444;border-radius:4px;}")
        layout.addWidget(self._news_reader_scroll)

    def _open_news_reader(self, nd):
        """Show news article as a full-screen tab (page 5)."""
        self._news_page_title.setText(nd.get("title", "Новина")[:60])
        # Rebuild content widget
        cw = QWidget()
        cw.setStyleSheet("background:#1a1a1a;")
        vl = QVBoxLayout(cw)
        vl.setContentsMargins(40, 28, 40, 28)
        vl.setSpacing(16)
        # Meta row
        mr = QHBoxLayout()
        cat = nd.get("category", "")
        if cat:
            cl2 = QLabel(cat)
            cl2.setStyleSheet("background:#1a2e1a;color:#4caf50;font-size:11px;"
                              "font-weight:bold;padding:3px 10px;border-radius:4px;")
            mr.addWidget(cl2)
        mr.addStretch()
        dl2 = QLabel(nd.get("date", ""))
        dl2.setStyleSheet("color:#555;font-size:12px;background:transparent;")
        mr.addWidget(dl2)
        vl.addLayout(mr)
        # Title
        tl = QLabel(nd.get("title", ""))
        tl.setWordWrap(True)
        tl.setStyleSheet("font-size:22px;font-weight:900;color:#fff;background:transparent;")
        vl.addWidget(tl)
        # Divider
        sp = QFrame(); sp.setFrameShape(QFrame.HLine)
        sp.setStyleSheet("background:#2a2a2a;border:none;max-height:1px;")
        vl.addWidget(sp)
        # Body text
        body = nd.get("body", nd.get("summary", ""))
        bl = QLabel(body)
        bl.setWordWrap(True)
        bl.setStyleSheet("font-size:14px;color:#ccc;background:transparent;")
        bl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        bl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        vl.addWidget(bl)
        # External link
        url = nd.get("url", "")
        if url:
            btn_link = QPushButton("🌐  Відкрити на сайті")
            btn_link.setStyleSheet("background:#1565c0;color:white;border:none;"
                                   "border-radius:6px;padding:8px 18px;font-weight:bold;")
            btn_link.clicked.connect(lambda: self._open_url(url))
            vl.addWidget(btn_link, 0, Qt.AlignLeft)
        vl.addStretch()
        self._news_reader_scroll.setWidget(cw)
        self.stacked_widget.setCurrentIndex(5)


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
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти"])
        btn_map = {
            "⚙ Налаштування": self.btn_settings,
            "👤 Аккаунти":     self.btn_accounts,
            "📁 Папка гри":    self.btn_folder,
            "🖼 Скріншоти":    self.btn_screens,
        }

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

        if style == "MetroUI":            # ── Full Metro: tile sidebar + flat UI ──
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

        elif style == "Round UI":
            self._apply_round_ui_style()

        else:
            # G9 UI — reset
            self._restore_normal_sidebar()
            self._apply_palette()

    def _apply_round_ui_style(self):
        """Round UI — акуратна тема з максимально округленими елементами,
        м’якими тінями та плавними градієнтами. Без Win32 blur-хаків, оскільки
        той підхід вимагав прав адміна і глючив на слабких GPU — тут саме чистий CSS.
        """
        acc  = getattr(self, "_color_accent",  "#4caf50")
        bg   = getattr(self, "_color_bg",      "#2b2b2b")
        side = getattr(self, "_color_sidebar", "#212121")

        # Скидаємо будь-який попередній WA_TranslucentBackground (від їхньої версії Aero)
        try:
            self.setAttribute(Qt.WA_TranslucentBackground, False)
        except Exception:
            pass

        def _hex_alpha(h, a):
            h = h.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r},{g},{b},{a})"

        def _lighten(h, factor=1.15):
            h = h.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, int(r * factor)); g = min(255, int(g * factor)); b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"

        def _darken(h, factor=0.8):
            h = h.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = int(r * factor); g = int(g * factor); b = int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"

        acc_light = _lighten(acc, 1.2)
        acc_dark = _darken(acc, 0.75)
        bg_light = _lighten(bg, 1.25)

        round_css = f"""
            QMainWindow, QWidget {{
                background: {bg};
                color: #f0f0f0;
            }}
            QGroupBox {{
                background: {_hex_alpha(bg_light, 200)};
                border: 1px solid {_hex_alpha(acc, 90)};
                border-radius: 14px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
                color: {acc_light};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 14px; padding: 0 6px;
                color: {acc_light};
            }}
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {acc_light}, stop:1 {acc});
                color: white;
                border: none;
                border-radius: 14px;
                padding: 9px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {_lighten(acc, 1.3)}, stop:1 {acc_light});
            }}
            QPushButton:pressed {{
                background: {acc_dark};
            }}
            QPushButton#PlayButton {{
                border-radius: 22px;
                font-size: 15px;
                padding: 12px;
            }}
            QPushButton#StopButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ef5350, stop:1 #c62828);
                border-radius: 22px;
            }}
            QPushButton#TitleBarBtn, QPushButton#TitleBarClose {{
                background: transparent; border: none;
                color: #bbb; font-size: 18px; padding: 0; border-radius: 12px;
            }}
            QPushButton#TitleBarBtn:hover {{ background: {_hex_alpha(acc, 60)}; color: white; }}
            QPushButton#TitleBarClose:hover {{ background: #c0392b; color: white; }}
            QTabWidget::pane {{
                background: {_hex_alpha(bg_light, 200)};
                border: 1px solid {_hex_alpha(acc, 70)};
                border-radius: 14px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {side};
                color: #999;
                padding: 9px 18px;
                border: none;
                border-radius: 12px 12px 0 0;
                margin-right: 3px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {acc};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                color: #ddd;
            }}
            QLineEdit, QTextEdit {{
                background: {_hex_alpha(bg_light, 220)};
                border: 1px solid {_hex_alpha(acc, 100)};
                border-radius: 10px;
                color: #eee;
                padding: 6px 10px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {acc_light};
            }}
            QComboBox {{
                background: {side};
                border: 1px solid {_hex_alpha(acc, 110)};
                border-radius: 10px;
                color: white;
                padding: 5px 10px;
            }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox QAbstractItemView {{
                background: {side};
                border: 1px solid {acc};
                border-radius: 8px;
                selection-background-color: {acc};
            }}
            QScrollBar:vertical {{
                background: transparent; width: 9px; margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {_hex_alpha(acc, 160)};
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {acc}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QLabel {{ background: transparent; color: #e8e8e8; }}
            QSlider::groove:horizontal {{
                background: {_hex_alpha(bg_light, 180)};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {acc_light};
                width: 20px; height: 20px;
                margin: -7px 0;
                border-radius: 10px;
                border: 3px solid {bg};
            }}
            QSlider::sub-page:horizontal {{ background: {acc}; border-radius: 3px; }}
            QProgressBar {{
                background: {_hex_alpha(bg_light, 180)};
                border: none;
                border-radius: 7px;
                text-align: center;
                color: transparent;
                height: 14px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {acc}, stop:1 {acc_light});
                border-radius: 7px;
            }}
            QListWidget {{
                background: {_hex_alpha(bg_light, 180)};
                border: 1px solid {_hex_alpha(acc, 80)};
                border-radius: 12px;
                color: #eee;
                padding: 4px;
            }}
            QListWidget::item {{
                border-radius: 8px;
                padding: 6px 8px;
            }}
            QListWidget::item:selected {{
                background: {acc};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background: {_hex_alpha(acc, 40)};
            }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border-radius: 8px;
                border: 2px solid {acc};
            }}
            QCheckBox::indicator:checked {{
                background: {acc};
            }}
        """
        self.setStyleSheet(round_css)
        self._restore_normal_sidebar()
        # Не викликаємо _apply_palette — вона перезаписатиме нашу тему

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
        }
        order = getattr(self, "_sidebar_button_order",
            ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти"])
        tiles_config = [tile_data[k] for k in order if k in tile_data]

        btn_map = {
            "Налаштування": self.btn_settings,
            "Аккаунти":     self.btn_accounts,
            "Папка гри":    self.btn_folder,
            "Скріншоти":    self.btn_screens,
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
        for b in [self.btn_settings, self.btn_accounts, self.btn_folder, self.btn_screens]:
            if b: b.show()

    # ── BACKGROUND IMAGE LOADER ──
    def _load_bg_from_url(self, url):
        """Download image from URL and set as background label pixmap."""
        def _fetch():
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "G9Launcher/1.5"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = r.read()
                QTimer.singleShot(0, lambda: self._set_bg_pixmap(data))
            except Exception:
                pass  # keep dark bg if load fails
        Thread(target=_fetch, daemon=True).start()

    def _set_bg_pixmap(self, data):
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull() and hasattr(self, '_bg_label'):
            self._bg_label.setPixmap(pix)


    # ── RESET ALL ──
    def _confirm_reset_all(self):
        """Скидання тільки налаштувань лаунчера (вигляд, кольори, конфіг)."""
        confirmed = CountdownConfirmDialog.ask(
            self,
            "Скидання лаунчера",
            "Ви впевнені, що хочете скинути ВСІ налаштування лаунчера до стандартних?\n\n"
            "Кольори, шрифт, розмір вікна, фон, порядок кнопок — все буде скинуто.\n"
            "Ігрові файли Minecraft (моди, сейви, версії) НЕ зачіпаються.",
            confirm_text="Скинути лаунчер",
            seconds=10,
        )
        if confirmed:
            self._reset_all_settings()
            QMessageBox.information(self, "Готово", "Налаштування лаунчера скинуто до стандартних.")

    def _confirm_reset_minecraft(self):
        """Скидання тільки ігрових файлів Minecraft (версії, моди, сейви, інстанси)."""
        confirmed = CountdownConfirmDialog.ask(
            self,
            "Скидання Minecraft",
            "Ви впевнені, що хочете ВИДАЛИТИ всі встановлені версії Minecraft, "
            "моди, сейви та ізольовані збірки?\n\n"
            "Ця дія НЕЗВОРОТНА. Ваші світи (saves) будуть втрачені, "
            "якщо ви не зробили резервну копію.\n"
            "Налаштування лаунчера (вигляд, кольори) НЕ зачіпаються.",
            confirm_text="Видалити Minecraft",
            seconds=10,
        )
        if confirmed:
            self._reset_minecraft_data()

    def _confirm_reset_everything(self):
        """Повне скидання — і Minecraft, і налаштувань лаунчера."""
        confirmed = CountdownConfirmDialog.ask(
            self,
            "Повне скидання",
            "Ви впевнені, що хочете скинути АБСОЛЮТНО ВСЕ?\n\n"
            "Будуть видалені: всі версії Minecraft, моди, сейви, ізольовані "
            "збірки, а також усі налаштування лаунчера (кольори, шрифт, фон).\n\n"
            "Ця дія НЕЗВОРОТНА.",
            confirm_text="Скинути ВСЕ",
            seconds=10,
        )
        if confirmed:
            self._reset_minecraft_data(show_message=False)
            self._reset_all_settings()
            QMessageBox.information(
                self, "Готово",
                "Повне скидання завершено. Minecraft та налаштування лаунчера "
                "повернуто до початкового стану."
            )

    def _reset_minecraft_data(self, show_message=True):
        """Видаляє всі ігрові дані Minecraft: versions, libraries, assets,
        instances (ізольовані збірки), minecraft/ (загальна папка), resources/.
        НЕ видаляє launcher_config.json та інші налаштування лаунчера."""
        # Зупиняємо гру, якщо вона запущена
        if getattr(self, "minecraft_process", None):
            try:
                self.minecraft_process.terminate()
            except Exception:
                pass
            self.minecraft_process = None
            self.is_playing = False

        targets = ["versions", "libraries", "assets", "instances",
                   "minecraft", "resources", "natives"]
        errors = []
        for name in targets:
            path = os.path.join(CONFIG_DIR, name)
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path, ignore_errors=False)
                except Exception as e:
                    errors.append(f"{name}: {e}")

        if hasattr(self, "_specs_loaded"):
            self._specs_loaded = False  # forces specs refresh next open

        try:
            self.refresh_version_combo()
        except Exception:
            pass

        if show_message:
            if errors:
                QMessageBox.warning(
                    self, "Частково виконано",
                    "Minecraft скинуто, але деякі файли не вдалося видалити "
                    "(можливо, гра ще запущена):\n\n" + "\n".join(errors)
                )
            else:
                QMessageBox.information(
                    self, "Готово",
                    "Всі дані Minecraft (версії, моди, сейви, збірки) видалено."
                )

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
        if hasattr(self, "chk_hide_on_launch"): self.chk_hide_on_launch.setChecked(True)

        # Ізоляція версій
        self._isolate_versions = True
        if hasattr(self, "chk_isolate_versions"):
            self.chk_isolate_versions.setChecked(True)

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
        default_order = ["⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти"]
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
                "hide_on_launch": self.chk_hide_on_launch.isChecked() if hasattr(self, "chk_hide_on_launch") else True,
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
                "isolate_versions": getattr(self, "_isolate_versions", True),
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
 
            # Restore sidebar order (фільтруємо видалені кнопки, наприклад 🌐 Сайт)
            _valid_btns = {"⚙ Налаштування", "👤 Аккаунти", "📁 Папка гри", "🖼 Скріншоти", "📦 Збірки"}
            saved_order = data.get("sidebar_button_order", [])
            saved_order = [b for b in saved_order if b in _valid_btns]
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

            # Restore version isolation toggle
            isolate = data.get("isolate_versions", True)
            self._isolate_versions = isolate
            if hasattr(self, "chk_isolate_versions"):
                self.chk_isolate_versions.setChecked(isolate)

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
        (50,  "Завантаження компонентів..."),
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
            QTimer.singleShot(200, advance_splash)
        else:
            QTimer.singleShot(120, do_launch)
 
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