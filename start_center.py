#!/usr/bin/env python3
"""Merkez yönetim uygulamasını başlatır."""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from common.settings import load_settings
from common import style
from common.style import build_qss
from common.database import Database, DatabaseError
from common.updater import check_for_update, install_event_filter
from common.mongo_startup import startup_check
from common.auto_updater import AutoUpdater
from center.main_window import CenterWindow


def main():
    # Windows/macOS yüksek DPI ekran desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Otomatik güncelleme - arka planda başlat
    updater = AutoUpdater("yazarkasa-merkez")
    updater.check_and_update_async()

    settings = load_settings()
    style.FONT_SCALE = settings.get("font_scale", 1.0)
    app.setStyleSheet(build_qss(settings.get("theme")))
    
    # MongoDB'yi otomatik başlat
    try:
        startup_check(settings["mongo_uri"])
    except Exception:
        pass

    db = Database(settings["mongo_uri"], settings["database_name"])
    try:
        db.verify_connection()
    except DatabaseError as error:
        err_str = str(error)
        if "DNS" in err_str or "NXDOMAIN" in err_str or "does not exist" in err_str:
            msg = ("Sunucuya bağlanılamadı: DNS hatası.\n\n"
                   "Lütfen internet bağlantınızı kontrol edin.\n"
                   "İnternet varsa ağınızın DNS ayarlarını 8.8.8.8 olarak değiştirin.")
        elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
            msg = ("Sunucuya bağlanılamadı: Zaman aşımı.\n\n"
                   "İnternet bağlantınızı kontrol edin.")
        else:
            msg = f"Veritabanı Hatası:\n{error}"
        QMessageBox.critical(None, "Bağlantı Hatası", msg)
        sys.exit(1)

    window = CenterWindow(db, settings)
    window.showMaximized()
    install_event_filter(app, window)
    check_for_update(window)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
