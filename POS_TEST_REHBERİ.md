#!/usr/bin/env python3
"""
POS Terminal Test Rehberi — Gerçek POS olmadan başlaç.

Üç seçenek:
  1. Simülasyon Modu — İçeri onayla/reddet butonu
  2. Mock Ingenico Sunucusu — Bilgisayarda POS simülasyonu
  3. Gerçek Ingenico — İstanbul'daki kasada test etme
"""

print("""
╔═══════════════════════════════════════════════════════════════╗
║           POS TERMINAL TEST REHBERİ                           ║
╚═══════════════════════════════════════════════════════════════╝

📋 SEÇENEK 1: SİMÜLASYON MODU (En Kolay)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gerçek terminal olmadan test et.

Adım 1: Bayi panelinde "⚙ POS Terminal Ayarları" butonuna tık
Adım 2: Bağlantı Modu: "simulate — Simülasyon (Test modu, gerçek POS yok)"
Adım 3: "💾 Kaydet"
Adım 4: Satış yap → "💳 KREDİ KARTI" → "SİMÜLASYON MODU" görünür
Adım 5: "✔ Onaylandı" / "✖ Reddedildi" ile test

Özellik: Sahte onay kodu üretilir, satış normal kaydedilir.


📋 SEÇENEK 2: MOCK İNGENICO SUNUCUSU (Gerçekçi Test)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bilgisayarında POS sunucusu çalıştır, kasa ona bağlansın.

TERMINAL 1 — Mock Sunucuyu Başlat:
  $ cd ~/Desktop/yazarkasa
  $ python3 ingenico_mock_server.py
  
  Çıktı olmalı:
  🖥  Mock Ingenico POS Sunucusu başlatılıyor...
  📡 Dinleme: 127.0.0.1:8400
  ✅ Sunucu çalışıyor. Kasa'dan gelen bağlantıları bekliyorum...

TERMINAL 2 (aynı PC'de) — Kasa Programı:
  $ cd ~/Desktop/yazarkasa
  $ python3 start_pos.py
  
  Kasa açılır → "⚙ POS Terminal Ayarları" → 
  • Mod: "ingenico — Ingenico iCT/Move serisi (TCP)"
  • IP: 127.0.0.1
  • Port: 8400
  • "🔌 Bağlantı Testi" → ✅ başarılı görünür
  • "💾 Kaydet"

TEST:
  1. Satış yap → "💳 KREDİ KARTI"
  2. Bekle — mock sunucu "Onaylı" yanıt döndürür
  3. Terminal 1'de görsün:
     [Bağlantı] 127.0.0.1:... bağlandı
     [İstek] 0200 - 123.45 ₺ (949)
     [Yanıt] Onaylı — Auth: 123456, Ref: 000000123456

✅ Başarılı, satış tamamlanır.


📋 SEÇENEK 3: GERÇEKİ İNGENICO (İstanbul Test)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gerçek terminali ayar:
  1. Terminal üzerinde: IP ve port ayarlarını bul
     (Genellikle yazıcı/konfigürasyon menüsünde)
  2. Terminal IP'si: 192.168.x.x (WiFi veya LAN)
  3. Port: 8400 (varsayılan Ingenico)
  
  4. Kasa "POS Terminal Ayarları":
     • Mod: "ingenico"
     • IP: [terminal'in IP'si]
     • Port: 8400
     • "🔌 Bağlantı Testi" → Cevap verir ise ✅
  
  5. "💳 KREDİ KARTI" ödeme yap → terminal ödeme alır

⚠️ SORUN GIDERİCİ:
━━━━━━━━━━━━━━━━━━

Bağlantı Testi ❌ ise:
  □ Terminal IP doğru mu? (ipconfig / ip addr ile kontrol et)
  □ Terminal açık mı? (rehber/başlat menüsü)
  □ Port doğru mu? (terminal ayarlarında kontrol et)
  □ Aynı WiFi/LAN'da mı? (PC ve terminal aynı ağda olmalı)
  □ Güvenlik duvarı? (Windows Defender/antivirus port 8400'ü kapa​bilir)

Güvenlik duvarı sorunuysa (Windows):
  1. Control Panel → Windows Defender Firewall → 
     "Windows Defender Firewall'u geçiş yap..." → "Tüm ayarları değiştir"
  2. "Gelen kuralları" → Yeni kural → Port 8400


🔗 ÖNEMLİ BİLGİLER:
━━━━━━━━━━━━━━━━━━━

• Simülasyon Modu → Hız testi için = 2 dakika
• Mock Sunucusu → Teknik sorun tespiti için = 15 dakika
• Gerçek Terminal → İstanbul'da = 5 dakika (test edip gönder)

Test geçtikten sonra: USB_PAKET/'deki exe'leri bayilere gönder.


HATA MESAJLARI REFERANSI:
━━━━━━━━━━━━━━━━━━━━━━

"Terminal IP adresi ayarlanmamış"
→ config.json'a terminal_host ekle veya dialog'dan gir

"Terminal zaman aşımı — müşteri ödeme yapmadı"
→ Terminal yanıt vermedi, 45 saniye bekledikten sonra timeout

"TCP 192.168.1.100:8400 bağlantısı başarılı"
→ ✅ Hazırız, ödeme alabiliriz


✅ TAMAMLAYIN:
━━━━━━━━━━━━

Hangisini test etmek istiyorsun?

  1. Simülasyon Modu (hızlı) — "Onayla/Reddet" butonu ile
  2. Mock Sunucusu (gerçekçi) — Bilgisayarda POS sunucusu
  3. Gerçek Terminal (İstanbul) — Gerçek Ingenico ile
""")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "1":
            print("\n✅ Simülasyon Modu seçildi.")
            print("Bayi panelinde '⚙ POS Terminal Ayarları' → Simülasyon → Kaydet")
        elif choice == "2":
            print("\n✅ Mock Sunucusu seçildi.")
            print("Çalıştır: python3 ingenico_mock_server.py")
            print("Sonra başka terminalde: python3 start_pos.py")
        elif choice == "3":
            print("\n✅ Gerçek Terminal seçildi.")
            print("Terminal IP adresini bul → POS Ayarları'na gir → Bağlantı Testi")
