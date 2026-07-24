# GivorPartners — Dağıtım, Güncelleme ve Kurulum Rehberi

## İçindekiler
1. [Genel Mimari](#1-genel-mimari)
2. [İlk Kurulum — Geliştirici Tarafı](#2-i̇lk-kurulum--geliştirici-tarafı)
3. [Exe Derleme (PyInstaller)](#3-exe-derleme-pyinstaller)
4. [Windows Installer Oluşturma (Inno Setup)](#4-windows-installer-oluşturma-inno-setup)
5. [Linux Paket Oluşturma (AppImage + .deb)](#5-linux-paket-oluşturma-appimage--deb)
6. [Bayilere Dağıtım](#6-bayilere-dağıtım)
7. [Güncelleme Yollama](#7-güncelleme-yollama)
8. [Otomatik Güncelleme Sistemi](#8-otomatik-güncelleme-sistemi)
9. [GitHub Actions ile Otomatik Derleme](#9-github-actions-ile-otomatik-derleme)
10. [Sorun Giderme](#10-sorun-giderme)

---

## 1. Genel Mimari

```
┌─────────────────────┐        ┌──────────────────────┐
│  GivorPartners      │        │  Bayi Kasa (POS)     │
│  Merkez (Center)    │        │  givorpartners-kasa  │
│  givorpartners-     │        │                      │
│  merkez.exe         │        │  Her bayiye ayrı     │
│                     │        │  bilgisayarda çalışır│
└─────────┬───────────┘        └──────────┬───────────┘
          │                               │
          └──────────── MongoDB ──────────┘
                  (Atlas Cloud veya
                   yerel sunucu)
```

- **Merkez**: Ürün/bayi yönetimi, raporlar, stok, analizler
- **Kasa**: Satış, ödeme, bayi-özel arayüz
- **MongoDB**: Her iki uygulama aynı DB'yi kullanır; Atlas ile internet üzerinden bağlanır

---

## 2. İlk Kurulum — Geliştirici Tarafı

```bash
# Proje klonla
git clone https://github.com/SENIN_KULLANICIN/givorpartners.git
cd givorpartners

# Bağımlılıkları yükle
pip install -r requirements.txt
pip install pyinstaller

# Örnek veri yükle
python sample_data.py

# Geliştirme modunda çalıştır
python start_center.py   # Merkez
python start_pos.py      # Bayi kasa
```

---

## 3. Exe Derleme (PyInstaller)

> **Önemli**: Her platform kendi exe'sini derler.
> Windows exe → Windows makinede, Linux AppImage → Linux makinede derlenir.

### Linux / macOS
```bash
cd ~/Desktop/yazarkasa

# Her ikisini birden
./build_all.sh

# Sadece kasa
./build_pos.sh

# Sadece merkez
./build_center.sh
```

### Windows
```cmd
cd C:\Users\KULLANICI\Desktop\yazarkasa
build_all.bat       # Her ikisi
build_pos.bat       # Sadece kasa
build_center.bat    # Sadece merkez
```

Çıktı: `dist/yazarkasa-kasa(.exe)` ve `dist/yazarkasa-merkez(.exe)`

---

## 4. Windows Installer Oluşturma (Inno Setup)

### Gereksinim
Inno Setup 6 — [innosetup.org](https://jrsoftware.org/isdl.php)

### Adımlar
1. Önce exe'leri derle (`build_all.bat`)
2. Inno Setup Compiler'ı aç
3. `installer/yazarkasa-setup.iss` dosyasını aç
4. **Derle** (Ctrl+F9)
5. Çıktı: `installer/Output/givorpartners-setup-v1.0.0.exe`

Bu setup.exe:
- Bayi bilgisayarına çift tıkla kurulur
- Başlat menüsüne kısayol ekler
- `config.json` (MongoDB bağlantısı) kurulum sırasında kopyalanır
- Otomatik kaldırma (Add/Remove Programs'dan)

---

## 5. Linux Paket Oluşturma (AppImage + .deb)

### AppImage (Tüm Linux dağıtımları)
```bash
# Önce exe'leri derle
./build_all.sh

# AppImage oluştur (appimagetool otomatik indirilir)
./installer/build_appimage.sh her ikisi
# veya:
./installer/build_appimage.sh kasa
./installer/build_appimage.sh merkez
```

Çıktı: `installer/givorpartners-kasa-v1.0.0.AppImage`

Bayi bilgisayarında:
```bash
chmod +x givorpartners-kasa-v1.0.0.AppImage
./givorpartners-kasa-v1.0.0.AppImage
```

### .deb Paketi (Ubuntu / Debian)
```bash
./installer/build_deb.sh her ikisi
```

Bayi bilgisayarında:
```bash
sudo dpkg -i givorpartners-kasa_1.0.0_amd64.deb
# Artık 'givorpartners-kasa' komutu çalışır
# Uygulamalar menüsünde de görünür
```

---

## 6. Bayilere Dağıtım

### Hazırlanacak Dosyalar

Her bayi için ayrı `config.json` hazırla:

```json
{
  "mongo_uri": "mongodb+srv://KULLANICI:SIFRE@CLUSTER.mongodb.net",
  "database_name": "yazarkasa",
  "dealer_code": "BAYI-001",
  "dealer_name": "İstanbul Şubesi",
  "theme": "night_mint",
  "font_scale": 1.0
}
```

### Windows Kurulum Paketi (Bayi Başına)
```
GivorPartners-BAYI001/
  ├── givorpartners-setup-v1.0.0.exe   ← setup (Inno Setup çıktısı)
  └── config.json                       ← bu bayiye özel ayarlar
```

Bayiye gönderilen talimat:
1. `givorpartners-setup-v1.0.0.exe` çalıştır
2. Kurulum sırasında sorarsa `config.json` dosyasının yolunu göster
3. Kurulum tamamlandıktan sonra `GivorPartners Kasa` masaüstünde görünür

### Linux Kurulum (AppImage — tercih edilen)
```bash
# Bayiye gönder:
givorpartners-kasa-v1.0.0.AppImage
config.json

# Bayide çalıştır:
chmod +x givorpartners-kasa-v1.0.0.AppImage
./givorpartners-kasa-v1.0.0.AppImage
```

### Toplu Dağıtım (Çok Sayıda Bayi)
```bash
# Her bayi için klasör oluştur
for dealer in BAYI001 BAYI002 BAYI003; do
    mkdir -p dist/$dealer
    cp installer/Output/givorpartners-setup-v1.0.0.exe dist/$dealer/
    # Bayiye özel config oluştur
    cat > dist/$dealer/config.json <<EOF
{
  "mongo_uri": "mongodb+srv://...",
  "dealer_code": "$dealer",
  "dealer_name": "..."
}
EOF
done
```

---

## 7. Güncelleme Yollama

### Adım 1 — Kodu Güncelle

```bash
# Sürüm numarasını güncelle
nano version.py
# VERSION = "1.0.1" olarak değiştir

# Değişiklikleri commit et
git add -A
git commit -m "v1.0.1: Hata düzeltmeleri + yeni özellikler"
git tag v1.0.1
git push origin main --tags
```

### Adım 2 — GitHub Actions Otomatik Derler

`v1.0.1` tagı push edilince GitHub Actions otomatik olarak:
- Windows exe + setup.exe derler
- Linux AppImage + .deb oluşturur
- `version.json` oluşturur
- Hepsini GitHub Releases'e yükler

**Yaklaşık süre**: 8-12 dakika

### Adım 3 — Güncelleme URL'sini Ayarla (Bir Kez Yapılır)

`version.py` içinde:
```python
UPDATE_CHECK_URL = "https://github.com/KULLANICI/givorpartners/releases/latest/download/version.json"
```

Bu URL her zaman en son sürümün `version.json`'unu döndürür.

### Adım 4 — Bayiler Otomatik Bildirim Alır

Bayi uygulamasını açtığında arka planda güncelleme kontrolü yapılır.
Yeni sürüm varsa:

```
┌─────────────────────────────────────────┐
│ 🔄 Güncelleme Mevcut — GivorPartners   │
│                                         │
│ Yeni sürüm v1.0.1 mevcut!              │
│ Mevcut sürümünüz: v1.0.0               │
│                                         │
│ v1.0.1 - 2026-07-24                    │
│ • Müşteri bilgisi isteğe bağlı          │
│ • Yazı boyutu ayarı eklendi             │
│                                         │
│ [Sonra Hatırlat]  [⬇ Şimdi Güncelle]  │
└─────────────────────────────────────────┘
```

"Şimdi Güncelle" tıklanınca:
1. Yeni exe indirilir (progress bar gösterilir)
2. Mevcut exe değiştirilir
3. Uygulama otomatik yeniden başlar

### Manuel Güncelleme (GitHub Actions Olmadan)

Eğer GitHub kullanmıyorsanız, kendiniz barındırabileceğiniz adımlar:

```bash
# 1. Exe'leri derle
./build_all.sh

# 2. version.json oluştur
python3 - <<'EOF'
import json
data = {
    "version": "1.0.1",
    "download_url_windows": "https://SUNUCUNUZ.com/updates/givorpartners-kasa-v1.0.1.exe",
    "download_url_linux":   "https://SUNUCUNUZ.com/updates/givorpartners-kasa-v1.0.1.AppImage",
    "changelog": "v1.0.1:\n• Hata düzeltmeleri"
}
with open("version.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
EOF

# 3. Dosyaları sunucuya yükle
scp dist/yazarkasa-kasa SUNUCU:/var/www/html/updates/givorpartners-kasa-v1.0.1.AppImage
scp version.json SUNUCU:/var/www/html/updates/version.json

# 4. version.py içinde UPDATE_CHECK_URL'yi güncelle
# UPDATE_CHECK_URL = "https://SUNUCUNUZ.com/updates/version.json"
```

---

## 8. Otomatik Güncelleme Sistemi

### Sistem Detayları

| Bileşen | Dosya | Açıklama |
|---------|-------|---------|
| Sürüm tanımı | `version.py` | `VERSION` + `UPDATE_CHECK_URL` |
| Güncelleme motoru | `common/updater.py` | İndirme + değiştirme + yeniden başlatma |
| Başlangıç entegrasyonu | `start_pos.py`, `start_center.py` | Arka planda güncelleme kontrolü |

### Güncelleme Akışı

```
Uygulama açılır
      │
      ▼ (arka plan thread)
UPDATE_CHECK_URL'den version.json indir
      │
      ├── Bağlantı hatası → sessizce devam et
      │
      └── Başarılı
            │
            ├── Sürüm aynı → hiçbir şey yapma
            │
            └── Yeni sürüm var
                  │
                  ▼
            Dialog göster (modal olmayan)
                  │
                  ├── "Sonra Hatırlat" → dialog kapanır
                  │
                  └── "Şimdi Güncelle"
                        │
                        ▼
                  exe indir (progress bar)
                        │
                        ▼
                  Mevcut exe → yeni exe
                        │
                        ▼
                  Uygulama yeniden başlar
```

### Platform Davranışı

| Platform | İndirme | Güncelleme Yöntemi |
|---------|---------|-------------------|
| Linux | AppImage URL | `shutil.move` → `os.execv` (anlık yeniden başlatma) |
| Windows | .exe URL | Batch script (taskkill + move + restart) |
| macOS | Linux URL (fallback) | `shutil.move` → `os.execv` |

---

## 9. GitHub Actions ile Otomatik Derleme

Workflow dosyası: `.github/workflows/build-release.yml`

### Tetikleme

```bash
# Yeni sürüm yayınla
git tag v1.0.1
git push origin v1.0.1
```

### Ne Üretilir?

```
GitHub Releases / v1.0.1
├── givorpartners-setup-v1.0.1.exe    ← Windows kurulum paketi
├── yazarkasa-merkez.exe              ← Windows merkez (bare exe)
├── yazarkasa-kasa.exe                ← Windows kasa (bare exe)
├── givorpartners-kasa-v1.0.1.AppImage    ← Linux (evrensel)
├── givorpartners-merkez-v1.0.1.AppImage  ← Linux merkez
├── givorpartners-kasa_1.0.1_amd64.deb   ← Ubuntu/Debian
├── givorpartners-merkez_1.0.1_amd64.deb
├── givorpartners-linux-v1.0.1.tar.gz    ← Linux genel arşiv
└── version.json                         ← Güncelleme kontrolü için
```

### GitHub Repository Kurulumu

```bash
# Repoyu oluştur ve ilk push
git init
git remote add origin https://github.com/KULLANICI/givorpartners.git
git add -A
git commit -m "İlk commit"
git push -u origin main

# İlk release
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions otomatik başlar
```

---

## 10. Sorun Giderme

### "Güncelleme bildirim gelmiyor"
- `version.py` içinde `UPDATE_CHECK_URL` tanımlı mı kontrol et
- `version.json` sunucuya erişilebilir mi: `curl UPDATE_CHECK_URL`
- `version.json`'daki sürüm, `version.py`'deki `VERSION`'dan büyük mü?

### "İndirme başarısız"
- URL'deki dosya mevcut mu kontrol et
- Güvenlik duvarı/antivirus indirmeyi engelliyor olabilir (Windows)
- İnternet bağlantısını kontrol et

### "Uygulama güncelleme sonrası açılmıyor" (Windows)
- `taskmgr` ile eski process'i öldür
- `dist/yazarkasa-kasa.exe` yolunun doğru olduğunu kontrol et
- Antivirus yeni exe'yi karantinaya almış olabilir → izin ver

### "AppImage çalışmıyor" (Linux)
```bash
# FUSE gereklidir
sudo apt install fuse libfuse2  # Ubuntu/Debian
sudo dnf install fuse           # Fedora

# AppImage'ı çalıştır
chmod +x givorpartners-kasa-v1.0.0.AppImage
./givorpartners-kasa-v1.0.0.AppImage
```

### "config.json bulunamadı"
- config.json'un exe ile aynı dizinde olduğunu kontrol et
- Varsayılan ayarlarla otomatik oluşturulur — MongoDB URI'yi güncelle

### Test Güncellemesi (Geliştirici için)

Gerçek güncelleme olmadan dialog'u test etmek için:

```python
# Python konsolunda
from common.updater import _show_update_dialog, UpdateChecker
c = UpdateChecker()
c.remote_version = "99.0.0"
c.changelog = "Test güncelleme\n• Yeni özellik A\n• Hata düzeltmesi B"
c.download_url = "https://example.com/test.exe"
_show_update_dialog(None, c)
```
