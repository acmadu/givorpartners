"""MongoDB otomatik başlatma — Podman / yerel MongoDB desteği."""
import subprocess
import time
import sys
import platform
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


def _is_mongodb_running(uri: str = "mongodb://127.0.0.1:27017", timeout_sec: int = 3) -> bool:
    """MongoDB sunucusunun erişilebilir olup olmadığını kontrol et."""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_sec * 1000)
        client.server_info()  # Bağlantı testi
        return True
    except Exception:
        return False


def ensure_mongodb_running(uri: str = "mongodb://127.0.0.1:27017") -> bool:
    """
    MongoDB'nin çalışmasını garanti et.
    Çalışmıyorsa:
      1. Podman yazarkasa-mongo kontayneri başlatmaya çalış
      2. Linux'ta systemctl mongod başlatmaya çalış
      3. 10 sn bekle ve yeniden kontrol et
    
    Başarılı: True, Başarısız: False
    """
    # Zaten çalışıyorsa OK
    if _is_mongodb_running(uri):
        print("[MongoDB] ✓ Zaten çalışıyor")
        return True

    print("[MongoDB] ⚠ Başlatılıyor...")
    system = platform.system()

    # ── Podman Kontayneri ──
    try:
        # Kontayner çalışıyor mu kontrol et
        result = subprocess.run(
            ["podman", "ps", "--filter", "name=yazarkasa-mongo", "--format", "{{.State}}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if "running" not in result.stdout.lower():
            # Çalışmıyor → başlat
            print("  • Podman kontayneri başlatılıyor...")
            subprocess.run(
                ["podman", "start", "yazarkasa-mongo"],
                capture_output=True,
                timeout=10,
            )
            time.sleep(2)  # Kontaynerin tam başlatılmasını bekle
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # Podman yüklü değil

    # ── Systemd MongoDB ──
    if system == "Linux" and _is_mongodb_running(uri) is False:
        try:
            print("  • Systemd mongod başlatılıyor...")
            subprocess.run(
                ["sudo", "systemctl", "start", "mongod"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(2)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # ── Kontrol Et ──
    for i in range(5):
        time.sleep(2)
        if _is_mongodb_running(uri):
            print(f"[MongoDB] ✓ Başlatıldı ({i + 1}. deneme)")
            return True

    print("[MongoDB] ✗ Başlatılamadı — manuel kontrol et")
    print(f"  • Podman: podman start yazarkasa-mongo")
    print(f"  • Linux:  sudo systemctl start mongod")
    print(f"  • Windows: Services → MongoDB başlat")
    return False


def startup_check(mongo_uri: str = "mongodb://127.0.0.1:27017"):
    """
    Uygulamayı açarken MongoDB'yi kontrol et.
    • Localhost MongoDB: Otomatik başlatmaya çalış
    • MongoDB Atlas (mongodb+srv://...): Kontrol atla (bulut hizmeti)
    Bağlantı başarısız → kullanıcıya dialog göster.
    """
    # MongoDB Atlas (bulut) ise, startup kontrol atla
    if "mongodb+srv://" in mongo_uri or "atlas" in mongo_uri.lower():
        return  # Bulut MongoDB zaten hazır
    
    if not _is_mongodb_running(mongo_uri):
        print("[Başlangıç] MongoDB bağlanılamıyor...")
        
        # Otomatik başlatmaya çalış
        if not ensure_mongodb_running(mongo_uri):
            # Başarısız
            try:
                from PyQt5.QtWidgets import QMessageBox, QApplication
                app = QApplication.instance()
                if not app:
                    app = QApplication([])
                
                msg = QMessageBox()
                msg.setWindowTitle("⚠ MongoDB Bağlantı Hatası")
                msg.setIcon(QMessageBox.Warning)
                msg.setText(
                    "MongoDB sunucusuna bağlanılamıyor.\n\n"
                    "Lütfen kontrol edin:\n"
                    "• Podman: podman start yazarkasa-mongo\n"
                    "• Linux: sudo systemctl start mongod\n"
                    "• Windows: MongoDB servisini başlat\n\n"
                    "Devam etmek için Tamam'ı tıklayın."
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            except Exception:
                pass
        else:
            print("[Başlangıç] ✓ MongoDB başarıyla başlatıldı")
