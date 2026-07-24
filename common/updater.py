"""Otomatik güncelleme sistemi — GivorPartners.

Nasıl çalışır:
  1. Uygulama açılışında UPDATE_CHECK_URL'deki version.json kontrol edilir.
  2. Yeni sürüm varsa bayi panelinde bildirim çıkar.
  3. "Güncelle" butonuna tıklanınca yeni exe indirilir ve uygulama yeniden başlatılır.

Sunucuda barındırılacak version.json formatı:
  {
    "version": "1.1.0",
    "download_url_windows": "https://example.com/releases/v1.1.0/givorpartners-kasa.exe",
    "download_url_linux":   "https://example.com/releases/v1.1.0/givorpartners-kasa",
    "download_url_mac":     "https://example.com/releases/v1.1.0/givorpartners-kasa.dmg",
    "changelog": "- Yeni özellik: ...\n- Hata düzeltmesi: ..."
  }
"""
import os
import platform
import shutil
import stat
import sys
import tempfile
import threading
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
import json

from version import VERSION, UPDATE_CHECK_URL


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def _current_exe() -> str:
    """Çalışan exe'nin tam yolunu döndür."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return ""


def _download_and_replace(url: str, progress_callback=None) -> bool:
    """
    Yeni exe'yi indir ve mevcut exe ile değiştir.
    İndirme tamamlanınca True döner.
    """
    exe_path = _current_exe()
    if not exe_path:
        return False  # Kaynak moddan çalışıyorsa güncelleme atla

    try:
        # Geçici dosyaya indir
        suffix = ".exe" if platform.system() == "Windows" else ""
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)

        def _reporthook(count, block_size, total_size):
            if progress_callback and total_size > 0:
                pct = min(100, int(count * block_size * 100 / total_size))
                progress_callback(pct)

        urlretrieve(url, tmp_path, reporthook=_reporthook)

        if platform.system() != "Windows":
            os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Windows'ta çalışan exe üzerine doğrudan yazılamaz — bat ile değiştir
        if platform.system() == "Windows":
            bat_path = tmp_path + "_update.bat"
            with open(bat_path, "w") as bat:
                bat.write(
                    f'@echo off\n'
                    f'ping -n 2 127.0.0.1 > nul\n'          # 1 sn bekle
                    f'move /Y "{tmp_path}" "{exe_path}"\n'
                    f'start "" "{exe_path}"\n'
                    f'del "%~f0"\n'
                )
            os.startfile(bat_path)
        else:
            # Linux/macOS: doğrudan üzerine yaz
            shutil.move(tmp_path, exe_path)
            os.execv(exe_path, sys.argv)  # Kendini yeniden başlat

        return True
    except Exception as e:
        print(f"[Güncelleme] İndirme hatası: {e}")
        return False


class UpdateChecker:
    """Güncelleme kontrolü + indirme yöneticisi."""

    def __init__(self):
        self.remote_version: str = ""
        self.download_url: str = ""
        self.changelog: str = ""
        self._data: dict = {}

    def fetch(self) -> bool:
        """version.json'u indir. Yeni sürüm varsa True döner."""
        if not UPDATE_CHECK_URL:
            return False
        try:
            with urlopen(UPDATE_CHECK_URL, timeout=6) as resp:
                self._data = json.loads(resp.read().decode())
        except Exception:
            return False

        self.remote_version = self._data.get("version", "0.0.0")
        self.changelog = self._data.get("changelog", "")

        system = platform.system()
        if system == "Windows":
            self.download_url = self._data.get("download_url_windows", "")
        elif system == "Darwin":
            self.download_url = self._data.get("download_url_mac", "")
        else:
            self.download_url = self._data.get("download_url_linux", "")

        return _version_tuple(self.remote_version) > _version_tuple(VERSION)


# Modül-düzeyinde paylaşılan checker örneği
_checker = UpdateChecker()


def check_for_update(parent_widget=None) -> None:
    """
    Açılışta arka planda güncelleme kontrolü yap.
    Yeni sürüm varsa UpdateDialog'u göster.
    parent_widget: ana pencere (QWidget), bildirim için kullanılır.
    """
    def _bg():
        if _checker.fetch():
            # Ana thread'de dialog aç
            from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.postEvent(app, _ShowUpdateEvent(parent_widget, _checker))

    threading.Thread(target=_bg, daemon=True).start()


# ── Güncelleme olayı ──────────────────────────────────────────
from PyQt5.QtCore import QEvent, QObject

_UPDATE_EVENT_TYPE = QEvent.registerEventType()


class _ShowUpdateEvent(QEvent):
    def __init__(self, parent, checker: UpdateChecker):
        super().__init__(QEvent.Type(_UPDATE_EVENT_TYPE))
        self.parent = parent
        self.checker = checker


def install_event_filter(app, parent_widget):
    """
    QApplication'a event filter yükle; güncelleme olayı gelince dialog aç.
    start_pos.py ve start_center.py'de çağrılır.
    """
    class _Filter(QObject):
        def eventFilter(self, obj, event):
            if event.type() == _UPDATE_EVENT_TYPE:
                _show_update_dialog(event.parent, event.checker)
                return True
            return False

    _f = _Filter()
    app.installEventFilter(_f)
    app._update_filter = _f  # GC'den korunması için referansı tut


def _show_update_dialog(parent, checker: UpdateChecker):
    """Güncelleme dialog'unu göster."""
    try:
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar,
            QHBoxLayout, QTextEdit,
        )
        from PyQt5.QtCore import Qt

        dlg = QDialog(parent)
        dlg.setWindowTitle("🔄 Güncelleme Mevcut — GivorPartners")
        dlg.setMinimumWidth(480)
        dlg.setModal(False)  # Kullanıcı ödeme sırasında değilse

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        lay.addWidget(QLabel(
            f"<b>Yeni sürüm v{checker.remote_version} mevcut!</b><br>"
            f"Mevcut sürümünüz: v{VERSION}",
            objectName="title"
        ))

        if checker.changelog:
            notes = QTextEdit()
            notes.setReadOnly(True)
            notes.setPlainText(checker.changelog)
            notes.setMaximumHeight(120)
            lay.addWidget(notes)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setVisible(False)
        lay.addWidget(progress)

        status_lbl = QLabel("")
        status_lbl.setObjectName("subtitle")
        lay.addWidget(status_lbl)

        btn_row = QHBoxLayout()
        later_btn = QPushButton("Sonra Hatırlat")
        later_btn.clicked.connect(dlg.reject)
        update_btn = QPushButton("⬇  Şimdi Güncelle", objectName="primary")

        def _do_update():
            update_btn.setEnabled(False)
            later_btn.setEnabled(False)
            progress.setVisible(True)
            status_lbl.setText("İndiriliyor...")

            def _progress(pct):
                progress.setValue(pct)

            def _run():
                ok = _download_and_replace(checker.download_url, _progress)
                if ok and platform.system() != "Windows":
                    # Linux/Mac: os.execv zaten yeniden başlattı
                    pass
                elif ok and platform.system() == "Windows":
                    status_lbl.setText("Güncelleme hazırlandı. Uygulama yeniden başlatılıyor...")
                    import time; time.sleep(1)
                    from PyQt5.QtWidgets import QApplication
                    QApplication.instance().quit()
                else:
                    status_lbl.setText("İndirme başarısız. İnternet bağlantınızı kontrol edin.")
                    update_btn.setEnabled(True)
                    later_btn.setEnabled(True)

            threading.Thread(target=_run, daemon=True).start()

        update_btn.clicked.connect(_do_update)
        btn_row.addWidget(later_btn)
        btn_row.addWidget(update_btn)
        lay.addLayout(btn_row)

        dlg.show()
    except Exception as e:
        print(f"[Güncelleme] Dialog hatası: {e}")

