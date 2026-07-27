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


def main():
    # Windows/macOS yüksek DPI ekran desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Otomatik güncelleme - arka planda başlat
    updater = AutoUpdater("yazarkasa-kasa")
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

    # ── Uzaktan yapılandırma ──
    dealer_code = settings.get("dealer_code", "")
    rcfg = remote_config.fetch(db.db, dealer_code)

    # Tema remote_config'ten geldiyse uygula
    if rcfg.get("theme"):
        settings["theme"] = rcfg["theme"]
        app.setStyleSheet(build_qss(rcfg["theme"]))

    # ── Zorunlu sürüm kontrolü (sync, uygulama açılmadan önce) ──
    if not check_min_version(rcfg.get("min_version")):
        sys.exit(0)

    login = LoginDialog(db)
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    window = PosWindow(db, login.dealer, settings)
    window.showMaximized()
    install_event_filter(app, window)

    # ── Arkaplanda: güncelleme kontrolü + AnyDesk ID ──
    check_for_update(window, auto_update=rcfg.get("auto_update", False),
                     min_version=rcfg.get("min_version"))

    def _bg_tasks():
        ad_id = anydesk.get_anydesk_id()
        if ad_id:
            remote_config.save_anydesk_id(db.db, dealer_code, ad_id)
    threading.Thread(target=_bg_tasks, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
