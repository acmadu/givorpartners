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
    # GivorPartners MongoDB Atlas — SRV yerine doğrudan sunucu adresleri
    # kullanılır; bazı modem/ISP'ler SRV (_mongodb._tcp) sorgusunu engelliyor.
    "mongo_uri": (
        "mongodb://givor_db:DsQ0IU5S8cV4OpPgAOPF@"
        "ac-m3m46tp-shard-00-00.odagxtj.mongodb.net:27017,"
        "ac-m3m46tp-shard-00-01.odagxtj.mongodb.net:27017,"
        "ac-m3m46tp-shard-00-02.odagxtj.mongodb.net:27017"
        "/?tls=true&replicaSet=atlas-p44ndh-shard-0&authSource=admin"
        "&retryWrites=true&w=majority"
        "&connectTimeoutMS=20000&serverSelectionTimeoutMS=20000"
        "&socketTimeoutMS=30000"
    ),
    "database_name": "yazarkasa",
    "dealer_code": "BAYI-001",
    "dealer_name": "Bayi",
    "theme": "light",
    "font_scale": 1.0,
    # Ödeme terminali — varsayılan: Ingenico Move 3000F
    "terminal_mode": "ingenico",   # manual | serial | tcp | ingenico
    "terminal_port": "",         # /dev/ttyUSB0  veya  COM3
    "terminal_baud": 9600,
    "terminal_host": "192.168.1.100",         # Ingenico TCP modu: terminal IP adresi
    "terminal_tcp_port": 6240,    # Ingenico Move 3000F: port 6240
}

# Eski (Türkçe) anahtarların İngilizce karşılıkları
LEGACY_KEYS = {
    "veritabani_adi": "database_name",
    "bayi_kodu": "dealer_code",
    "bayi_adi": "dealer_name",
}


# Kurulum şablonundan gelen sahte (örnek) bağlantı adresi işaretleri
PLACEHOLDER_MARKERS = ("USERNAME", "PASSWORD", "CLUSTER.mongodb.net",
                       "<", "example.com")


def _is_placeholder_uri(uri: str) -> bool:
    if not uri or not uri.strip():
        return True
    return any(marker in uri for marker in PLACEHOLDER_MARKERS)


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
    try:
        with open(CONFIG_FILE, encoding="utf-8") as file:
            settings = json.load(file)
    except (json.JSONDecodeError, OSError):
        # Bozuk config → varsayılanlara dön
        save_settings(dict(DEFAULT_SETTINGS))
        return dict(DEFAULT_SETTINGS)
    # Eski Türkçe anahtarları İngilizce'ye taşı
    migrated = False
    for old_key, new_key in LEGACY_KEYS.items():
        if old_key in settings:
            settings.setdefault(new_key, settings.pop(old_key))
            migrated = True
    # Eksik anahtarları varsayılanlarla tamamla
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)
    # Kurulum şablonundaki örnek adres kaldıysa gerçek adresle değiştir
    if _is_placeholder_uri(settings.get("mongo_uri", "")):
        settings["mongo_uri"] = DEFAULT_SETTINGS["mongo_uri"]
        migrated = True
    if migrated:
        save_settings(settings)
    return settings
