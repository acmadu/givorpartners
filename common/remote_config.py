"""Uzaktan yapılandırma sistemi.

MongoDB'deki `remote_configs` koleksiyonundan ayarları çeker ve
yerel config.json ile birleştirir.

Koleksiyon şeması:
  {
    "target": "*",           # Tüm bayiler VEYA "BAYI-001" gibi belirli bir bayi
    "theme": "amber",        # Tema (light, amber, ocean, night_mint)
    "announcement": "...",   # Zorunlu duyuru metni (None ise yok)
    "min_version": "1.0.1",  # Bu sürümden düşükse güncelleme zorunlu
    "auto_update": true,     # True → sessiz otomatik güncelleme
  }

Öncelik sırası: bayi özel > wildcard (*) > yerel config
"""

import logging

log = logging.getLogger(__name__)

# Varsayılan değerler — DB bağlantısı yoksa bunlar geçerli
_DEFAULTS = {
    "theme": None,          # None → yerel config'ten al
    "announcement": None,
    "min_version": None,
    "auto_update": False,
}

_cached: dict | None = None   # Uygulama ömrünce önbellek


def fetch(db, dealer_code: str) -> dict:
    """
    MongoDB'den remote config'i çeker, yerel default'larla birleştirir.
    db  : pymongo Database nesnesi (bağlantı yoksa None geçilebilir)
    Döndürdüğü dict her zaman tam anahtarlara sahiptir (_DEFAULTS şeması).
    """
    global _cached
    if _cached is not None:
        return _cached

    result = dict(_DEFAULTS)

    if db is None:
        _cached = result
        return result

    try:
        col = db["remote_configs"]

        # Önce wildcard (*) belgesi
        wildcard = col.find_one({"target": "*"}, {"_id": 0})
        if wildcard:
            for k in _DEFAULTS:
                if k in wildcard and wildcard[k] is not None:
                    result[k] = wildcard[k]

        # Sonra bayiye özgü belge (varsa override eder)
        specific = col.find_one({"target": dealer_code}, {"_id": 0})
        if specific:
            for k in _DEFAULTS:
                if k in specific and specific[k] is not None:
                    result[k] = specific[k]

        log.info(f"Remote config alındı: {result}")
    except Exception as e:
        log.warning(f"Remote config alınamadı (yerel ayarlar kullanılıyor): {e}")

    _cached = result
    return result


def clear_cache():
    """Önbelleği temizle (test veya yeniden bağlantı için)."""
    global _cached
    _cached = None


def save_anydesk_id(db, dealer_code: str, anydesk_id: str):
    """Bayinin AnyDesk ID'sini MongoDB dealers koleksiyonuna yazar."""
    if db is None or not anydesk_id:
        return
    try:
        db["dealers"].update_one(
            {"code": dealer_code},
            {"$set": {"anydesk_id": anydesk_id}},
        )
        log.info(f"AnyDesk ID kaydedildi: {anydesk_id}")
    except Exception as e:
        log.warning(f"AnyDesk ID kaydedilemedi: {e}")
