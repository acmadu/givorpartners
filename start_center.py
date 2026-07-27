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


def _install_excepthook():
    """Beklenmeyen hatalarda çirkin PyInstaller penceresi yerine
    kullanıcı dostu uyarı gösterir."""
    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        try:
            QMessageBox.critical(
                None, "Beklenmeyen Hata",
                f"Bir hata oluştu:\n\n{exc_value}\n\n"
                "Uygulamayı yeniden başlatın. Sorun devam ederse yetkiliye bildirin.")
        except Exception:
            pass
    sys.excepthook = hook


def main():
    # Windows/macOS yüksek DPI ekran desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    _install_excepthook()

    # Otomatik güncelleme - arka planda başlat
    try:
        AutoUpdater("yazarkasa-merkez").check_and_update_async()
    except Exception:
        pass

    settings = load_settings()
    style.FONT_SCALE = settings.get("font_scale", 1.0)
    app.setStyleSheet(build_qss(settings.get("theme")))
    
    # MongoDB'yi otomatik başlat
    try:
        startup_check(settings["mongo_uri"])
    except Exception:
        pass

    try:
        db = Database(settings["mongo_uri"], settings["database_name"])
        db.verify_connection()
    except DatabaseError as error:
        QMessageBox.critical(None, "Bağlantı Hatası", str(error))
        sys.exit(1)
    except Exception as error:
        QMessageBox.critical(
            None, "Bağlantı Hatası",
            "Sunucuya bağlanılamadı.\n\n"
            "• İnternet bağlantınızı kontrol edin\n"
            "• Modem/router DNS ayarını 8.8.8.8 yapın\n\n"
            f"Detay: {error}")
        sys.exit(1)

    window = CenterWindow(db, settings)
    window.showMaximized()
    install_event_filter(app, window)
    try:
        check_for_update(window)
    except Exception:
        pass
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
