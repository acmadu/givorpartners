"""Otomatik güncelleme sistemi."""

import json
import os
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path

from version import VERSION, UPDATE_CHECK_URL


def _safe_log(message):
    """Türkçe karakterler bazı Windows konsollarında (cp1252/charmap)
    UnicodeEncodeError'a yol açıp arka plan thread'ini çökertebiliyor.
    Bu yüzden print() yerine hatayı yutan güvenli bir log kullanılır."""
    try:
        print(message)
    except Exception:
        try:
            print(message.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass


class AutoUpdater:
    """GitHub Releases'ten otomatik güncelleme."""
    
    def __init__(self, app_name="yazarkasa-kasa"):
        """
        app_name: "yazarkasa-kasa" veya "yazarkasa-merkez"
        """
        self.app_name = app_name
        self.exe_name = f"{app_name}.exe"
        self.current_version = VERSION
        self.is_updating = False
    
    def check_for_updates(self):
        """GitHub Releases'ten yeni version var mı kontrol et."""
        if not UPDATE_CHECK_URL:
            return None
        
        try:
            response = urllib.request.urlopen(UPDATE_CHECK_URL, timeout=5)
            data = json.loads(response.read().decode())
            
            latest_version = data.get("version")
            download_url = data.get(f"{self.app_name}_setup_url")
            
            if not latest_version or not download_url:
                return None
            
            if self._compare_versions(latest_version, self.current_version) > 0:
                return {
                    "version": latest_version,
                    "url": download_url,
                    "exe_name": data.get("setup_exe_name", f"{self.app_name}-setup-v{latest_version}.exe")
                }
            return None
        except Exception as e:
            _safe_log(f"[AutoUpdater] Guncelleme kontrolu hatasi: {e}")
            return None
    
    def _compare_versions(self, v1, v2):
        """v1 > v2 ise 1, eşitse 0, v1 < v2 ise -1 döndür."""
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    
    def download_and_install(self, update_info):
        """Güncellemeleri indir ve yükle."""
        if self.is_updating:
            return False
        
        self.is_updating = True
        
        try:
            url = update_info["url"]
            exe_name = update_info["exe_name"]
            temp_dir = Path(os.getenv("TEMP", "/tmp")) / "yazarkasa_update"
            temp_dir.mkdir(exist_ok=True)
            
            exe_path = temp_dir / exe_name
            
            _safe_log(f"[AutoUpdater] {url} indiriliyor...")
            urllib.request.urlretrieve(url, exe_path)
            
            _safe_log(f"[AutoUpdater] Yukleme baslatiliyor: {exe_path}")
            subprocess.Popen(
                [str(exe_path), "/SILENT", "/NORESTART"],
                shell=False
            )
            
            # Başarı
            return True
            
        except Exception as e:
            _safe_log(f"[AutoUpdater] Guncelleme hatasi: {e}")
            self.is_updating = False
            return False
    
    def check_and_update_async(self, on_update_available=None):
        """Arka planda güncelleme kontrol et. on_update_available callback."""
        def _check():
            try:
                update_info = self.check_for_updates()
                if update_info:
                    _safe_log(f"[AutoUpdater] Yeni version {update_info['version']} bulundu")
                    if on_update_available:
                        on_update_available(update_info)
                    # Otomatik olarak indir ve yükle
                    self.download_and_install(update_info)
            except Exception as e:
                _safe_log(f"[AutoUpdater] Async kontrol hatasi: {e}")
        
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
