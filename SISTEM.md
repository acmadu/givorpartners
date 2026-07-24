# Yazar Kasa Sistemi — Genel Dokümantasyon

Merkezi yönetimli, çok bayili yazar kasa (POS) sistemi.
**PyQt5** masaüstü arayüzleri + **MongoDB** veritabanı. Linux ve Windows'ta çalışır.

---

## 1. Genel Mimari

```
                    ┌─────────────────────┐
                    │      MongoDB        │
                    │  (Podman/Docker or  │
                    │   uzak sunucu)      │
                    └─────┬─────────┬─────┘
                          │         │
        ┌─────────────────┴──┐   ┌──┴──────────────────────┐
        │  MERKEZ YÖNETİM    │   │  KASA (POS)             │
        │  start_center.py   │   │  start_pos.py           │
        │                    │   │                         │
        │  • Genel bakış     │   │  • Bayi girişi (şifre)  │
        │  • Ürün yönetimi   │   │  • Barkod okutma        │
        │  • Stok grafiği    │   │  • Sepet + ödeme        │
        │  • Satış analizi   │   │  • Koli barkodu         │
        │  • Bayi hesapları  │   │  • Kamera ile karekod   │
        │  • Satış raporları │   │    (isteğe bağlı)       │
        └────────────────────┘   └─────────┬───────────────┘
                                           │ USB (klavye emülasyonu)
                                 ┌─────────┴───────────────┐
                                 │  Masaüstü Barkod        │
                                 │  Okuyucu (sabit)        │
                                 └─────────────────────────┘
```

- **Merkez**: ürünleri/bayileri yönetir, tüm satışları ve carileri raporlar.
- **Kasa**: her bayide çalışır; kendi hesabıyla giriş yapar, satışları merkeze (ortak veritabanına) yazar.
- Birden fazla kasa aynı anda çalışabilir; hepsi aynı MongoDB'ye bağlanır.

## 2. Dosya Yapısı

| Yol | Görev |
|---|---|
| `start_center.py` | Merkez yönetim uygulamasını başlatır |
| `start_pos.py` | Kasa uygulamasını başlatır (önce giriş ekranı) |
| `sample_data.py` | Örnek ürün/bayi/hesap verisi yükler |
| `config.json` | Ayarlar: `mongo_uri`, `database_name`, `theme`… (izin: 600) |
| `common/settings.py` | Ayar okuma/yazma, eski anahtar göçü |
| `common/style.py` | 4 tema (Gece Nanesi, Okyanus, Kehribar, Aydınlık) + QSS |
| `common/database.py` | MongoDB katmanı: CRUD, kimlik doğrulama, analiz sorguları, eski Türkçe şema göçü |
| `center/main_window.py` | Merkez ana pencere, gezinme, tema seçici |
| `center/page_dashboard.py` | Genel bakış kartları + son satışlar |
| `center/page_products.py` | Ürün ekle/düzenle/sil (koli barkodu dahil) |
| `center/page_stock.py` | Stok çubuk grafiği, kritik/az stok eşikleri |
| `center/page_analytics.py` | Günlük ciro, cari (bayi) dağılımı, ödeme türü grafikleri |
| `center/page_dealers.py` | Bayi kartları + kasa giriş hesapları |
| `center/page_reports.py` | Tarih/bayi filtreli satışlar, çift tıkla kalem detayı |
| `pos/login_dialog.py` | Bayi girişi (5 hatalı denemede 30 sn kilit) |
| `pos/main_window.py` | Kasa ekranı: barkod, sepet, ödeme |
| `pos/barcode_camera.py` | Kamera ile karekod/barkod okuma (isteğe bağlı) |

## 3. Barkod Okuyucu Sistemi

### 3.1 Nasıl çalışır?

USB barkod okuyucuların tamamına yakını **HID klavye emülasyonu** ile çalışır:
bilgisayara taktığınızda sistem onu bir klavye sanır. Okuyucu, barkodu
"yazıp" sonuna **Enter** basar. Bu yüzden:

- **Sürücü gerekmez** — Linux (Fedora dahil) ve Windows'ta tak-çalıştır.
- **Programda özel bağlantı gerekmez** — kasa ekranındaki barkod kutusu
  `Enter` ile tetiklenir.
- Uygulamada **tuş yakalama** vardır: odak sepette veya bir butonda olsa
  bile okutulan barkod otomatik olarak barkod kutusuna yönlenir.
  Yani kasiyer neye tıklamış olursa olsun okutma kaybolmaz.
- Okuyucunuz Enter yerine **Tab** soneki gönderiyorsa o da desteklenir.

Akış:

```
Okuyucu barkodu görür → "8690000000011" + Enter tuşlar → barcode_input doldu
→ _barcode_scanned() → veritabanında ürün/koli barkodu aranır
→ sepete eklenir (koli ise koli içi adet kadar) → stok yetersizse uyarı
```

### 3.2 Hangi cihazı almalıyım? (masaya sabit)

Masaya sabit kullanım için **çok yönlü (omnidirectional) masaüstü** okuyucu
alın: ürünü elinizle önünden geçirirsiniz, tetik basmak gerekmez, barkodun
açısı önemli olmaz. Öneriler (TR piyasasında bulunanlar):

| Sınıf | Model | Özellik | Yaklaşık fiyat* |
|---|---|---|---|
| **Önerilen** | **Honeywell Orbit MK/MS7120** | Sektör standardı masaüstü lazer, 1D, çok dayanıklı | 4.000–6.000 ₺ |
| Önerilen (2D) | **Zebra DS9308** | 1D+2D (karekod da okur), çok hızlı, ekrandan da okur | 6.000–9.000 ₺ |
| Üst seviye | **Datalogic Magellan 800i** | 1D+2D, market kasası sınıfı | 8.000–12.000 ₺ |
| Ekonomik | **Newland FR27 Urchin** | 1D+2D masaüstü, uygun fiyat/performans | 3.000–5.000 ₺ |
| Bütçe | **Sunlux/Henex/Perkon masaüstü 2D** modelleri | 1D+2D, giriş seviyesi | 1.500–3.000 ₺ |

\* Fiyatlar değişkendir; sadece sınıf farkını göstermek içindir.

**Karar rehberi:**
- Sadece klasik ürün barkodu (EAN-13) okutacaksanız **1D lazer (Orbit)** yeter.
- Karekod (QR), telefon ekranından kupon vb. de okuyacaksanız **2D imager
  (DS9308 / FR27)** alın. *Bugünden 2D almak geleceğe yatırımdır.*
- Bağlantı: **USB (HID klavye modu)** olsun — RS232 sürümünü almayın.

### 3.3 Okuyucu ayarı (ilk kurulum)

Okuyucular kutudan genelde doğru ayarla çıkar. Değilse, kılavuzundaki şu
yapılandırma barkodlarını okutun:

1. **USB Keyboard (HID)** modu
2. Sonek (suffix): **Enter (CR)** — Tab da desteklenir
3. Klavye düzeni **US** seçin (Türkçe Q'da bazı modeller sayıları yanlış
   basabilir; US en garantisidir, barkodlar sadece rakam içerir)

**Test:** Bir metin düzenleyici açın, barkod okutun. Barkod rakamları tek
satırda görünüp imleç alt satıra iniyorsa (Enter geldi) hazırsınız.

### 3.4 Koli barkodu

Üründe `koli barkodu` + `koli içi adet` tanımlıysa, koli barkodu
okutulduğunda sepete tek seferde o kadar ürün eklenir
(ör. koli barkodu okutuldu → 24 × su şişesi).

### 3.5 Kamera ile okuma (yedek yöntem)

`opencv-python` + `pyzbar` (ve sistemde `zbar`) kuruluysa kasada
**📷 Kamera** butonu belirir; web kamerasıyla karekod/barkod okunabilir.
Sabit okuyucunun yedeği olarak düşünün, hızı onun yerini tutmaz.

```bash
pip install opencv-python pyzbar
sudo dnf install zbar        # Fedora
```

## 4. Veritabanı Şeması (MongoDB — "yazarkasa")

### products
```js
{ barcode: "8690000000011", name: "Su 0.5L", price: 15.0, vat: 20,
  stock: 120, box_barcode: "...", box_quantity: 24, active: true }
```
### dealers
```js
{ code: "BAYI-001", name: "Merkez Şube", address: "...", phone: "...",
  active: true,
  // kasa giriş hesabı (merkezden açılır):
  username: "bayi1", password_hash: "<pbkdf2>", salt: "<hex>" }
```
### sales
```js
{ dealer_code: "BAYI-001", date: ISODate(...), payment_type: "NAKİT",
  total: 45.0,
  items: [{ barcode, name, quantity, unit_price }] }
```

İndeksler: `barcode` (tekil), `code` (tekil), `username` (tekil, kısmi),
`date`, `dealer_code`. Eski Türkçe koleksiyon/alan adları ilk bağlantıda
otomatik göç ettirilir.

## 5. Güvenlik Özellikleri

| Önlem | Açıklama |
|---|---|
| PBKDF2-SHA256 parola özeti | 100.000 tur + kullanıcı başına tuz; düz metin parola saklanmaz |
| Giriş kilidi | 5 hatalı denemede 30 sn kilit (kaba kuvvete karşı) |
| Zamanlama-güvenli doğrulama | Kullanıcı yokken de sahte özet hesaplanır; yanıt süresinden kullanıcı adı sızmaz |
| Regex enjeksiyonu koruması | Ürün aramasında girdi `re.escape` ile etkisizleştirilir |
| config.json izni | POSIX'te `600` — Mongo URI kimlik bilgisi diğer kullanıcılardan gizli |
| Parola politikası | Yeni hesap parolaları en az 6 karakter |
| Hata dayanıklılığı | Bağlantı koptuğunda uygulama çökmez; satış kaydedilemezse **sepet korunur** |

## 6. MongoDB Kurulum Seçenekleri

### A. Podman/Docker (Yerel, En Basit) — **ÖNERİLEN**
```bash
# Kurulum (ilk defa)
podman run -d --name yazarkasa-mongo -p 27017:27017 \
  -v yazarkasa-mongo-veri:/data/db mongo:7

# Sonraki açılışlarda
podman start yazarkasa-mongo
```
✅ **Avantaj**: Yazılım yönetimi kolay, başka PC'de aynı yapılır
❌ **Dezavantaj**: Podman/Docker kurulu olmalı; Linux/Mac için doğal, Windows da mümün

### B. MongoDB Community Server (Doğrudan Kurulum)
Masaüstü bilgisayarlar için "sistem servisi" gibi kurulur:

**Windows**: [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
- Setup wizard ile kurulum, otomatik sistem servisi olarak başlar
- `config.json`: `"mongo_uri": "mongodb://localhost:27017"` kalır

**Linux (Fedora)**:
```bash
sudo dnf install mongodb-community-server
sudo systemctl start mongod        # başlat
sudo systemctl enable mongod       # her açılışta otomatik
```

✅ **Avantaj**: Sade, sistem servisi; container overhead yok
❌ **Dezavantaj**: Her PC'ye ayrı kurma; Windows'da 400 MB+ ek gerek

### C. Cloud Veritabanı (MongoDB Atlas)
Bulut tabanlı çözüm — sunucu yönetimi hazır:

1. [atlas.mongodb.com](https://www.mongodb.com/cloud/atlas) hesap aç (ücretsiz)
2. Cluster oluştur (free tier: 512 MB)
3. `config.json` güncelle:
```json
{
  "mongo_uri": "mongodb+srv://kullanıcı:şifre@cluster.mongodb.net",
  "database_name": "yazarkasa"
}
```

✅ **Avantaj**: Sunucu kurulumu yok; internet her yerden erişim
❌ **Dezavantaj**: Internet gerekli, gecikme başka sunucunun bağlantısı kadar

### D. Kuruluş Sunucusu (Ağ Merkezi)
Merkez ofiste sunucu varsa (Windows Server, Linux):
```json
{
  "mongo_uri": "mongodb://SUNUCU_IP:27017",
  "database_name": "yazarkasa"
}
```

---

## 7. Kurulum Adımları

### Seçenek 1: Kaynak Koddan (Geliştirici)
```bash
# 1) Depo indir
git clone https://github.com/... yazarkasa
cd yazarkasa

# 2) Bağımlılıklar
pip install -r requirements.txt

# 3) MongoDB başlat (A seçeneği — Podman)
podman run -d --name yazarkasa-mongo -p 27017:27017 \
  -v yazarkasa-mongo-veri:/data/db mongo:7

# 4) Örnek veri yükle
python sample_data.py          # bayi1 / 123456

# 5) Çalıştır
python start_center.py         # terminal 1
python start_pos.py            # terminal 2
```

### Seçenek 2: Exe'den (Son Kullanıcı — Windows/Linux)

**Hazırlama** (depo sahibi):
```bash
cd yazarkasa
chmod +x build_all.sh          # Linux/Mac
./build_all.sh                 # veya build_all.bat (Windows)
```
Oluşan exe'ler: `dist/yazarkasa-merkez(.exe)` ve `dist/yazarkasa-kasa(.exe)`

**Kuruluşun Bilgisayarına Dağıt**:
```
yazarkasa/
  ├─ yazarkasa-merkez(.exe)
  ├─ yazarkasa-kasa(.exe)
  └─ config.json              ← MongoDB URI'i buradan ayarla
```

**İlk Çalıştırma**:
1. MongoDB başlat (seçeneğinize göre)
2. `yazarkasa-merkez` → verileri yükle, ürün ekle
3. `yazarkasa-kasa` → bayi giriş

---

## 8. Dağıtım (Distribution)

## 7. Kısayollar ve İpuçları

- **F11**: tam ekran (her iki uygulamada), **Esc**: tam ekrandan çık (merkez)
- Tema: merkez kenar çubuğundaki açılır kutudan; seçim `config.json`'a kaydedilir
- Satış Raporları'nda satıra **çift tık** → kalem detayları
- Satış Analizi'nde dönem: **7 / 30 / 90 gün**
- Kasada barkod kutusuna elle barkod yazıp **Enter** ile de ürün eklenebilir
- Masaya sabit barkod okuyucu: odak tabloda/butonsa bile okutulan barkod otomatik barkod kutusuna yönlenir
