# 🚀 BAYILERE DEPLOYMENT REHBERI — Uzaktan Yönetim + Otomatik Güncelleme

**Bu rehber:** Bayilerdeki POS cihazlarına GivorPartners yazarkasa kurulumu, yapılandırması ve uzaktan yönetimini kapsar.

**Hazırlayan:** GivorPartners Teknik Ekibi  
**Versiyon:** 1.0.0  
**Tarih:** 26 Temmuz 2026

---

## 📋 İçerik
1. [Sistem Gereksinimler](#sistem-gereksinimler)
2. [Kurulum Adımları](#kurulum-adımları)
3. [İlk Konfigürasyon](#ilk-konfigürasyon)
4. [Uzaktan Yönetim Nasıl Çalışır?](#uzaktan-yönetim-nasıl-çalışır)
5. [Ödeme Terminali Kurulumu](#ödeme-terminali-kurulumu)
6. [Sorun Çözme](#sorun-çözme)
7. [Destek İletişimi](#destek-iletişimi)

---

## 🖥️ Sistem Gereksinimler

### Minimum Donanım
- **İşletim Sistemi:** Windows 10/11 (64-bit) veya Linux (Fedora/Ubuntu)
- **RAM:** 4 GB
- **Disk:** 500 MB
- **İnternet:** Sabit/WiFi (MongoDB Atlas bağlantısı için)
- **Ödeme Terminali:** Ingenico veya TCP destekli terminal (isteğe bağlı)

### Yazılım
- **Python 3.8+:** (EXE içinde gömülü, ayrıca kurmaya gerek yok)
- **Ağ Bağlantısı:** 
  - Merkez sunucusu: `givor.odagxtj.mongodb.net` (MongoDB Atlas)
  - Ödeme Terminali: `127.0.0.1:8400` (yerel) veya `terminal_ip:8000` (ağ)

---

## 📥 Kurulum Adımları

### 1️⃣ EXE Dosyasını İndir
GitHub Releases sayfasından indir:
```
https://github.com/acmadu/givorpartners/releases
```
**Dosya:** `yazarkasa-kasa-v1.0.0.exe` (Windows) veya `yazarkasa-kasa` (Linux)

### 2️⃣ Antivirus Uyarısı (Windows)
Windows Defender uyarı verebilir ("Tanınmayan yayıncı"):
1. Uyarı penceresinde **"Yine de çalıştır"** butonuna tıkla
2. Açılış ekranında **"Daha fazla bilgi"** → **"Yine de çalıştır"** seç

**Neden:** PyInstaller ile derlenen uygulamalar bazen uyarı tetikler.

### 3️⃣ Masaüstüne Kısayol Oluştur
EXE dosyasına sağ tık → **"Kısayol Gönder"** → **"Masaüstü"**  
Kısayol adını değiştir: `GivorPartners Kasa`

### 4️⃣ Başlat ve Giriş Yap
1. EXE dosyasını çift tıkla
2. Giriş ekranında:
   - **Kullanıcı Adı:** `bayi1`
   - **Şifre:** `123456`
3. **"Giriş Yap"** butonuna tıkla

---

## ⚙️ İlk Konfigürasyon

### POS Terminal Ayarları

Ödeme terminali üzerinden ödeme alacaksanız ayarlamalısınız:

#### **Adım 1: Ayarlar Menüsünü Aç**
- Ana kasa penceresinde **"⚙ POS Terminal Ayarları"** butonuna tıkla

#### **Adım 2: Terminal Modunu Seç**
Terminal tipine göre seç:

| Mod | Açıklama | Kullanım |
|-----|----------|---------|
| **Manual** | UI butonlarla ödeme girişi | Test/Demo |
| **Simülasyon** | Gerçek olmayan ödeme (test) | Eğitim |
| **Ingenico** | TCP/IP üzerinden Ingenico | Üretim (En çok kullanılan) |
| **TCP Genel** | Herhangi bir TCP terminali | Diğer markaların terminalleri |
| **Serial/COM** | USB port üzerinden | Eski terminaller |

#### **Adım 3: Ingenico TCP Yapılandırması (En Yaygın)**

**Eğer TCP üzerinde Ingenico kullanacaksanız:**

1. **Terminal Modu:** "ingenico" seç
2. **Terminal IP Adresi:** Ingenico terminalinin ağdaki IP adresini gir
   - Nasıl bulunur? Terminale `....*23` (yönetici kodu) gir
3. **Port:** 8400 (varsayılan, değiştirme)
4. **Bağlantı Test Et:** "🔗 Test" butonuna tıkla
   - ✅ Başarılı: "Terminale bağlantı başarılı"
   - ❌ Hata: Aşağıdaki "Sorun Çözme" kısmını incele

#### **Adım 4: Ayarları Kaydet**
**"Kaydet"** butonuna tıkla. Sistem yeniden başlayacak.

---

## 🛰️ Uzaktan Yönetim Nasıl Çalışır?

### Otomatik Güncelleme Sistemi

Aşağıdaki durumlarda **otomatik olarak** güncelleme uygulanır:

#### 1. **Zorunlu Güncelleme** (Uygulama Açılmadan Önce)
Merkez yöneticisi bir minimum sürüm belirlediyse:
- Bayi POS açıldığında sürüm kontrol edilir
- Sürümü yetersizse **"⛔ Güncelleme Zorunlu"** dialog açılır
- **"⬇  Güncelle ve Yeniden Başlat"** otomatik yapılır
- Bayi müdahalesine gerek yok

#### 2. **Sessiz Otomatik Güncelleme**
Merkez tarafından `auto_update` etkinleştirilmişse:
- Her gün açılışta yeni sürüm kontrol edilir
- Varsa **hiç soru sormadan** indirilir ve uygulanır
- Bayi fark etmeyebilir (arka planda)

#### 3. **Normal Güncelleme Bildirimi**
- POS'un sağ üst kısmında **"🔄 Güncelleme Mevcut"** mesajı çıkar
- **"Güncelle"** butonuna tıklanabilir
- **"Sonra Hatırlat"** ile ertelenebilir

### Uzaktan Ayarlar (Remote Config)

Merkez yönetici bu ayarları uzaktan belirleyebilir:

| Ayar | Etki | Örnek |
|------|------|-------|
| **Tema** | Bayi panelinin renk şeması değişir | ocean, night_mint, amber |
| **Otomatik Güncelleme** | Yeni sürümler otomatik uygulanır | True/False |
| **Minimum Sürüm** | Gereken sürüm altıysa güncelleme zorunlu | 1.0.5 |
| **Duyuru Metni** | Ekranda uyarı mesajı gösterilir | "Bakım saati: Pazartesi 02:00" |

**Bu ayarlar nasıl uygulanır?**
1. Merkez yönetici ayarları veritabanında belirler
2. Bayi POS açıldığında otomatik olarak indirilir
3. Hiç müdahale gerekmez — her açılışta güncellenir

---

## 🏧 Ödeme Terminali Kurulumu

### Ingenico Terminal Kurulumu (Adım Adım)

#### **Öncesi:** Terminal Hazırlığı
1. Ingenico terminalini elektriğe tak
2. İnternet bağlantısını kontrol et (WiFi/LAN)
3. Terminal IP adresini öğren:
   - Terminalde `.....*23` tuş kodu gir (yönetici)
   - Ağ ayarlarında IP adresini bul
   - Not et: örn. `192.168.1.100`

#### **Sırasında:** GivorPartners Yapılandırması
1. **"⚙ POS Terminal Ayarları"** → **"Ingenico (TCP)"** seç
2. **Terminal IP:** `192.168.1.100` gir (terminallden aldığın)
3. **Port:** `8400` (değiştirme)
4. **"🔗 Test Et"** butonuna tıkla
5. ✅ Sonuç: **"Bağlantı başarılı — Terminal hazır"**

#### **Sonrası:** Ödeme Testi
1. Ürün seçip satış yap
2. Ödeme ekranında **"Kart ile Ödeme"** seç
3. Tutar gösteriliyor → **"Onayla"**
4. Terminal otomatik olarak ödeme isteği gönderir
5. Müşteri kartını okuttur
6. Terminal onaylı/reddedili yanıt verir

---

## 🔍 Sorun Çözme

### ❌ "Terminale Bağlanılamıyor"

**Nedeni:** Terminal IP'si yanlış veya ağ sorunu

**Çözüm:**
1. Terminal IP'sini tekrar kontrol et:
   ```
   Terminalde: .....*23 → Ağ Ayarları → IP Adresi
   ```
2. Bağlantıyı kontrol et:
   - POS bilgisayarı ile terminal **aynı WiFi/LAN'da mı?**
   - Güvenlik duvarı (firewall) 8400 portunu engel mi?
3. Terminal restart et:
   - Terminali kapat, 30 sn bekle, aç
4. GivorPartners'ı kapıp açıl

### ❌ "Veritabanı bağlantısı yok"

**Nedeni:** İnternet yok veya MongoDB Atlas erişim problemi

**Çözüm:**
1. İnternet bağlantısını kontrol et:
   ```bash
   # Windows: Komut İsteminde
   ping google.com
   ```
2. Firewall MongoDB Atlas portunu açtı mı?
   - Config.json'daki **mongo_uri** doğru mu?
3. VPN kullanıyorsan VPN'yi aç

### ❌ Uygulama açılmıyor / Beyaz ekran

**Nedeni:** Python kütüphaneleri yüklenmedi (EXE'yi doğru indirmedin)

**Çözüm:**
1. GitHub Releases'den yeni EXE indir
2. Eski versiyonun çöpü:
   - `build/` ve `dist/` klasörlerini sil
3. Yeni EXE çalıştır

### ❌ Güncelleme "İndir" basıldı ama devamı yok

**Nedeni:** İnternet kesitme veya update sunucusu erişim yok

**Çözüm:**
1. İnternet kontrol et
2. Tekrar dene
3. Hâlâ başarısız → **Teknik Desteğe Ulaş**

### ❌ Ödeme İşlem sırasında "Timeout"

**Nedeni:** Terminal yanıt vermiyor

**Çözüm:**
1. Terminal bağlantısını kontrol et
2. Terminal restart et
3. **"Reddet"** butonuna tıkla ve müşteriye hata söyle
4. İşlemi yeniden başlat

---

## 📞 Destek İletişimi

### Teknik Sorunlar
- **Email:** support@givorpartners.com
- **Telefon:** +90 (XXX) XXX XX XX
- **Chat:** WhatsApp / Telegram (link verilecek)

### Destek Vermek İçin Gereken Bilgiler
Sorun yaşadığında aşağıdakileri paylaş:
1. **Hata Mesajı:** Tam olarak ne yazıyor?
2. **Sürüm:** "⚙ Ayarlar" → "Hakkında" → Sürüm numarası
3. **Terminal Tipi:** Ingenico mi, TCP mi, Manual mi?
4. **Sistem:** Windows mi, Linux mi?
5. **İnternet:** Sabit mi, WiFi mi?

### Acil Müdahale (Remote Connection)

Sorun çözmek için uzaktan bağlanabiliriz:
1. **AnyDesk Kurulumu:** Windows'ta `https://anydesk.com` → İndir → Kur
2. **ID'ni Gönder:** Yazarkasa açtığında otomatik yer alır
3. **Merkez Yönetici:** "🛰 Uzaktan Yönetim" → "Bayiler" → AnyDesk butonuyla bağlan

---

## ✅ İlk Açılış Kontrol Listesi

POS'u açmadan önce şunları kontrol et:

- [ ] **Bilgisayar:** Başlattı, login yaptı
- [ ] **İnternet:** Aktif (WiFi/LAN)
- [ ] **Terminal:** Elektriğe takıp, IP adresini öğrendin
- [ ] **Config:** Terminal IP GivorPartners'da girdi, test başarılı ✅
- [ ] **MongoDB:** "Veritabanı hazır" mesajı gösteriliyor
- [ ] **Bayi Giriş:** bayi1 / 123456 ile giriş yaptı
- [ ] **Ana Ekran:** Ürün listesi gösteriliyor

---

## 🎓 Hızlı Referans

### En Sık Kullanılan Butonlar
| Buton | İşlevi | Kullanım |
|-------|--------|---------|
| 🛍️ Ürün Ekle | Sepete ürün ekle | Her satışta |
| 💳 Kart ile Ödeme | Kredi kartı alır | Kart ödemeleri |
| 🧾 Makbuz Yazdır | Fatura yazdırır | Satış bitişinde |
| ↩️ İade | Ödemeyi geri al | Müşteri talebi |
| ⚙️ Ayarlar | Terminal yapılandırması | Kurulumda 1x |
| 🚪 Çıkış | POS'tan çıkış | Vardiya bitişinde |

### Sık Yapılan İşlemler
1. **Ürün Satış:**
   - 🛍️ Seç → Miktar → Ödeme Türü → 💳 veya 💵 → ✅
2. **İade Yap:**
   - ↩️ Seç → Tutar → Onay → ✅
3. **Rapor Görüntüle:**
   - 📊 Günlük Satış → Tarih Seç → Görüntüle

---

## 📖 Ek Kaynaklar
- **Sistem Mimarisi:** `SISTEM.md`
- **Kurulum Rehberi:** `KURULUM_REHBERI.md`
- **Sorun Çözme:** `TEST_SEÇENEKLERI.txt`

---

**Not:** Bu rehber düzenli olarak güncellenir. En son sürüm için `github.com/acmadu/givorpartners` ziyaret et.

