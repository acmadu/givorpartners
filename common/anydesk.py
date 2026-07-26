"""AnyDesk ID tespiti ve MongoDB'ye kaydı.

Bayi bilgisayarında AnyDesk yüklüyse ID'yi okuyup MongoDB'ye yazar.
Merkez panelinde bayiler listesinde bu ID görünür.

AnyDesk komut satırı:
  anydesk --get-id          → mevcut ID'yi stdout'a basar (tüm platformlar)
  AnyDesk.exe --get-id      → Windows
"""

import subprocess
import platform
import logging
import shutil

log = logging.getLogger(__name__)


def _find_anydesk_exe() -> str | None:
    """AnyDesk'in yolunu bul. Bulamazsa None döner."""
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
            r"C:\Program Files\AnyDesk\AnyDesk.exe",
        ]
        for c in candidates:
            import os
            if os.path.isfile(c):
                return c
        # PATH'te var mı?
        found = shutil.which("AnyDesk")
        return found
    else:
        # Linux / macOS
        return shutil.which("anydesk")


def get_anydesk_id() -> str | None:
    """
    AnyDesk'i çalıştırıp ID'yi döndür.
    AnyDesk kurulu değilse veya hata oluşursa None döner.
    """
    exe = _find_anydesk_exe()
    if not exe:
        log.info("AnyDesk kurulu değil, ID alınamadı.")
        return None

    try:
        result = subprocess.run(
            [exe, "--get-id"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        anydesk_id = result.stdout.strip()
        if anydesk_id.isdigit():
            log.info(f"AnyDesk ID: {anydesk_id}")
            return anydesk_id
        log.warning(f"AnyDesk geçersiz ID döndürdü: {anydesk_id!r}")
    except subprocess.TimeoutExpired:
        log.warning("AnyDesk --get-id zaman aşımı")
    except Exception as e:
        log.warning(f"AnyDesk ID alınamadı: {e}")

    return None
