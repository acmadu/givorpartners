#!/bin/bash
# ============================================================
#  GivorPartners — Çalıştırma Rehberi
# ============================================================

cat << 'EOF'

╔════════════════════════════════════════════════════════════╗
║         GivorPartners — Exe Çalıştırma Rehberi            ║
╚════════════════════════════════════════════════════════════╝

▶ 1️⃣  EXE DERLEME (Bir kez yapılır)

  ┌─ Linux / macOS ──────────────────────────────┐
  │  $ cd ~/Desktop/yazarkasa                    │
  │  $ ./build_all.sh                            │
  │                                              │
  │  Çıktı:                                      │
  │    dist/yazarkasa-kasa        (Bayi)         │
  │    dist/yazarkasa-merkez      (Merkez)       │
  └──────────────────────────────────────────────┘

  ┌─ Windows ────────────────────────────────────┐
  │  > cd C:\Users\KULLANICI\Desktop\yazarkasa   │
  │  > build_all.bat                             │
  │                                              │
  │  Çıktı:                                      │
  │    dist\yazarkasa-kasa.exe                   │
  │    dist\yazarkasa-merkez.exe                 │
  └──────────────────────────────────────────────┘

▶ 2️⃣  MONGODB BAŞLATMA

  ┌─ Seçenek A: Podman (Mevcut) ─────────────────┐
  │  $ podman start yazarkasa-mongo              │
  │  $ podman ps | grep yazarkasa-mongo          │
  │  Bağlantı: mongodb://127.0.0.1:27017        │
  └──────────────────────────────────────────────┘

  ┌─ Seçenek B: MongoDB Atlas (Cloud) ───────────┐
  │  config.json içinde:                         │
  │  "mongo_uri": "mongodb+srv://USER:PASS@..." │
  │  (İnternet bağlantısı yeterli)               │
  └──────────────────────────────────────────────┘

  ┌─ Seçenek C: Yerel MongoDB (Yüklü ise) ──────┐
  │  Linux:   $ sudo systemctl start mongod      │
  │  Windows: MongoDB Services'ten başlat        │
  └──────────────────────────────────────────────┘

▶ 3️⃣  EXE ÇALIŞTIRUN

  ┌─ Linux / macOS ──────────────────────────────┐
  │  Merkez:  $ dist/yazarkasa-merkez            │
  │  Kasa:    $ dist/yazarkasa-kasa              │
  │                                              │
  │  Veya çift tıkla dosyaya (file manager)      │
  └──────────────────────────────────────────────┘

  ┌─ Windows ────────────────────────────────────┐
  │  Çift tıkla:                                 │
  │    dist\yazarkasa-kasa.exe                   │
  │    dist\yazarkasa-merkez.exe                 │
  │                                              │
  │  Veya komut satırından:                      │
  │  > dist\yazarkasa-kasa.exe                   │
  │  > dist\yazarkasa-merkez.exe                 │
  └──────────────────────────────────────────────┘

▶ 4️⃣  CONFIG AYARLANMAMIŞSA

  Kod gibi çalışan ilk kez:
    ✅ config.json otomatik oluşturulur
    ⚠️  MongoDB bağlantısı başarısız
    
  Çözüm:
    1. config.json aç
    2. mongo_uri güncelle:
       "mongo_uri": "mongodb://127.0.0.1:27017"
       (veya MongoDB Atlas URL'niz)
    3. Exe'yi yeniden çalıştır

═══════════════════════════════════════════════════════════════

💡 İPUÇLARı:

  • Bayi (kasa) açıldığında giriş ekranı → bayi1 / 123456
  • Merkez açıldığında doğrudan açılır (admin, şifresiz)
  • Güncelleme kontrolü arka planda çalışır (ilk açılıştan ~5 sn sonra)
  • F11 ile tam ekran modu

EOF
