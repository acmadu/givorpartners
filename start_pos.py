#!/usr/bin/env python3
"""Bayi kasa (POS) uygulamasını başlatır — bayi girişiyle açılır."""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from common.settings import load_settings
from common import style
from common.style import build_qss
from common.database import Database, DatabaseError
from common.updater import check_for_update, install_event_filter
from common.mongo_startup import startup_check
from pos.login_dialog import LoginDialog
from pos.main_window import PosWindow


def main():
    # Windows/macOS yüksek DPI ekran desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    settings = load_settings()
    style.FONT_SCALE = settings.get("font_scale", 1.0)
    app.setStyleSheet(build_qss(settings.get("theme")))
    
    # MongoDB'yi otomatik başlat
    startup_check(settings["mongo_uri"])
    
    db = Database(settings["mongo_uri"], settings["database_name"])
    try:
        db.verify_connection()
    except DatabaseError as error:
        QMessageBox.critical(None, "Veritabanı Hatası", str(error))
        sys.exit(1)

    login = LoginDialog(db)
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    window = PosWindow(db, login.dealer, settings)
    window.show()
    install_event_filter(app, window)
    check_for_update(window)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
