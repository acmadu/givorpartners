#!/usr/bin/env python3
"""Bayi kasa (POS) uygulamasını başlatır — bayi girişiyle açılır."""
import sys
import threading

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from common.settings import load_settings
from common import style
from common.style import build_qss
from common.database import Database, DatabaseError
from common.updater import check_for_update, install_event_filter, check_min_version
from common.mongo_startup import startup_check
from common import remote_config
from common import anydesk
from common.auto_updater import AutoUpdater
from pos.login_dialog import LoginDialog
from pos.main_window import PosWindow


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
        AutoUpdater("yazarkasa-kasa").check_and_update_async()
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

    # ── Uzaktan yapılandırma ──
    dealer_code = settings.get("dealer_code", "")
    try:
        rcfg = remote_config.fetch(db.db, dealer_code)
    except Exception:
        rcfg = {}

    # Tema remote_config'ten geldiyse uygula
    if rcfg.get("theme"):
        settings["theme"] = rcfg["theme"]
        app.setStyleSheet(build_qss(rcfg["theme"]))

    # ── Zorunlu sürüm kontrolü (sync, uygulama açılmadan önce) ──
    try:
        if not check_min_version(rcfg.get("min_version")):
            sys.exit(0)
    except SystemExit:
        raise
    except Exception:
        pass

    login = LoginDialog(db)
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    window = PosWindow(db, login.dealer, settings)
    window.showMaximized()
    install_event_filter(app, window)

    # ── Arkaplanda: güncelleme kontrolü + AnyDesk ID ──
    try:
        check_for_update(window, auto_update=rcfg.get("auto_update", False),
                         min_version=rcfg.get("min_version"))
    except Exception:
        pass

    def _bg_tasks():
        try:
            ad_id = anydesk.get_anydesk_id()
            if ad_id:
                remote_config.save_anydesk_id(db.db, dealer_code, ad_id)
        except Exception:
            pass
    threading.Thread(target=_bg_tasks, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
