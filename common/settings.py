"""Application settings — read from config.json."""
import json
import os
import stat
import sys

# PyInstaller ile derlendiyse exe'nin yanında, aksi halde proje kökünde
if getattr(sys, "frozen", False):
    PROJECT_DIR = os.path.dirname(sys.executable)
else:
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")

DEFAULT_SETTINGS = {
    # GivorPartners MongoDB Atlas — tüm konumlarda otomatik bağlanır
    "mongo_uri": "mongodb+srv://givor_db:DsQ0IU5S8cV4OpPgAOPF@givor.odagxtj.mongodb.net/?retryWrites=false&w=majority&connectTimeoutMS=30000&serverSelectionTimeoutMS=30000&socketTimeoutMS=30000&tlsAllowInvalidCertificates=true",
    "database_name": "yazarkasa",
    "dealer_code": "BAYI-001",
    "dealer_name": "Bayi",
    "theme": "light",
    "font_scale": 1.0,
    # Ödeme terminali
    "terminal_mode": "manual",   # manual | serial | tcp | ingenico
    "terminal_port": "",         # /dev/ttyUSB0  veya  COM3
    "terminal_baud": 9600,
    "terminal_host": "",         # TCP modu: terminal IP adresi
    "terminal_tcp_port": 8000,
}

# Eski (Türkçe) anahtarların İngilizce karşılıkları
LEGACY_KEYS = {
    "veritabani_adi": "database_name",
    "bayi_kodu": "dealer_code",
    "bayi_adi": "dealer_name",
}


def save_settings(settings: dict):
    """Ayarları config.json dosyasına yazar (yalnız sahibi okuyabilir)."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)
    if os.name == "posix":
        # mongo_uri kimlik bilgisi içerebilir; diğer kullanıcılardan gizle
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def load_settings() -> dict:
    """Ayarları yükler; dosya yoksa varsayılanlarla oluşturur."""
    if not os.path.exists(CONFIG_FILE):
        save_settings(dict(DEFAULT_SETTINGS))
        return dict(DEFAULT_SETTINGS)
    with open(CONFIG_FILE, encoding="utf-8") as file:
        settings = json.load(file)
    # Eski Türkçe anahtarları İngilizce'ye taşı
    migrated = False
    for old_key, new_key in LEGACY_KEYS.items():
        if old_key in settings:
            settings.setdefault(new_key, settings.pop(old_key))
            migrated = True
    # Eksik anahtarları varsayılanlarla tamamla
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)
    if migrated:
        save_settings(settings)
    return settings
