#!/usr/bin/env python3
"""
Hızlı test senaryosu — Config'i test moduna ayarlayıp kasa başlat.

Kullanım:
  python3 test_pos_quick.py [mode]
  
Modlar:
  simulate  → Simülasyon (onayla/reddet butonu)
  mock      → Mock Ingenico sunucusu (başka terminal gerekli)
"""

import json
import subprocess
import sys
import os

CONFIG_FILE = "config.json"


def set_terminal_mode(mode: str) -> bool:
    """Config'deki terminal_mode'u değiştir."""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        config["terminal_mode"] = mode
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Config güncellendi: terminal_mode = {mode}")
        return True
    except Exception as e:
        print(f"❌ Config hatası: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("""
╔════════════════════════════════════════════════════╗
║  POS TERMİNAL TEST — Hızlı Başlama                ║
╚════════════════════════════════════════════════════╝

Kullanım:
  python3 test_pos_quick.py simulate   — Simülasyon modu
  python3 test_pos_quick.py mock       — Mock Ingenico (sunucu gerekli)
  python3 test_pos_quick.py real       — Gerçek Terminal ayarları

Örnek:
  $ python3 test_pos_quick.py simulate
  ✅ Config güncellendi: terminal_mode = simulate
  🔄 Kasa başlatılıyor...
""")
        return

    mode = sys.argv[1].lower()
    
    if mode == "mock":
        print("""
╔════════════════════════════════════════════════════╗
║  MOCK İNGENİCO SUNUCUSU BAŞLATMA                  ║
╚════════════════════════════════════════════════════╝

TERMINAL 1'de bu komutu çalıştır:
  python3 ingenico_mock_server.py

TERMINAL 2'de (bu pencere):
  python3 test_pos_quick.py mock

Sunucu başladığında kasa açılır.
Test: Satış yap → Kredi Kartı → Otomatik onay alırsın.
""")
        input("\nMock sunucusu çalışıyor mu? (ENTER devam...)")
        if not set_terminal_mode("ingenico"):
            return
        print('✅ Ingenico modu aktif, terminal_host: 127.0.0.1, port: 8400')
    
    elif mode == "simulate":
        print("""
╔════════════════════════════════════════════════════╗
║  SİMÜLASYON MODU                                   ║
╚════════════════════════════════════════════════════╝

✅ Simülasyon modu etkinleştiriliyor...
🔄 Kasa başlatılıyor...

Açılınca:
  • Satış yap
  • "💳 KREDİ KARTI" butonuna tık
  • "SİMÜLASYON MODU" yazısı görünür
  • "✔ Onaylandı" / "✖ Reddedildi" - birini seç
  • Test tamamlanır!
""")
        if not set_terminal_mode("simulate"):
            return
    
    elif mode == "real":
        print("""
╔════════════════════════════════════════════════════╗
║  GERÇEK INGENICO TERMİNAL                          ║
╚════════════════════════════════════════════════════╝

Adımlar:
  1. Terminal üzerinde ayarlar bölümüne gir
  2. IP adresi ve port ayarlarını bul (genelde 8400)
  3. Kasa açılınca "⚙ POS Terminal Ayarları" tık
  4. Terminal IP'sini gir
  5. "🔌 Bağlantı Testi" ile doğrula
  6. Satış yap

Kasa şimdi Ingenico modunda başlatılıyor...
""")
        if not set_terminal_mode("ingenico"):
            return
    
    else:
        print(f"❌ Bilinmeyen mod: {mode}")
        print("Modlar: simulate, mock, real")
        return

    # Kasa başlat
    print("\n🔄 Kasa başlatılıyor...\n")
    try:
        subprocess.run([sys.executable, "start_pos.py"], check=False)
    except Exception as e:
        print(f"❌ Kasa başlatılamadı: {e}")


if __name__ == "__main__":
    main()
