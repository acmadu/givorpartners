# Yazar Kasa Sistemi

Merkezden yönetilen, MongoDB tabanlı yazar kasa (POS) sistemi.
İki masaüstü uygulamadan oluşur:

| Uygulama | Dosya | Açıklama |
|---|---|---|
| **Merkez Yönetim** | `start_center.py` | Ürün, bayi, stok grafiği ve satış raporu yönetimi |
| **Kasa (POS)** | `start_pos.py` | Bayilerdeki satış ekranı, barkod okuma |

## Kurulum

```bash
# 1. Bağımlılıklar
pip install -r requirements.txt

# 2. MongoDB'nin çalıştığından emin olun (Fedora)
sudo dnf install mongodb-org        # veya Docker: docker run -d -p 27017:27017 mongo
sudo systemctl start mongod

# 3. (İsteğe bağlı) Örnek verileri yükleyin
python sample_data.py
```

## Çalıştırma

```bash
python start_center.py   # Merkez yönetim paneli
python start_pos.py      # Bayi kasa ekranı
```

Her iki pencerede **F11** tam ekrana geçirir (merkezde **Esc** çıkarır).

## Yapılandırma — config.json

İlk çalıştırmada otomatik oluşturulur:

```json
{
  "mongo_uri": "mongodb://localhost:27017",
  "database_name": "yazarkasa",
  "dealer_code": "BAYI-001",
  "dealer_name": "Örnek Bayi"
}
```

- Bayilerdeki kasalarda `mongo_uri` merkez sunucunun adresini göstermelidir
  (örn. `mongodb://192.168.1.10:27017` veya MongoDB Atlas bağlantısı).
- Her bayide `dealer_code` / `dealer_name` o bayiye göre ayarlanmalıdır.
- Eski Türkçe anahtarlar (`veritabani_adi`, `bayi_kodu`, `bayi_adi`)
  ilk açılışta otomatik olarak yeni adlara taşınır.

## Barkod Okuma

- **USB barkod okuyucu:** Klavye gibi davranır; kasa ekranında odak sürekli
  barkod kutusundadır, okutulan barkod otomatik işlenir.
- **Koli barkodu:** Ürün kartında koli barkodu ve koli içi adet tanımlanır.
  Koli barkodu okutulduğunda ürünler tek tek okutulmadan koli adedi kadar
  sepete eklenir.
- **Kamera ile okuma (isteğe bağlı):**

  ```bash
  sudo dnf install zbar            # Fedora (Windows'ta gerekmez)
  pip install opencv-python pyzbar
  ```

  Kurulunca kasa ekranında "📷 Kamera" butonu görünür.

## Proje Yapısı

```
yazarkasa/
├── start_center.py         # Merkez uygulama girişi
├── start_pos.py            # Kasa uygulama girişi
├── sample_data.py          # Örnek veri yükleyici
├── config.json             # Yerel ayarlar (otomatik oluşur)
├── common/
│   ├── settings.py         # Ayar yönetimi
│   ├── database.py         # MongoDB katmanı (+ eski şema göçü)
│   └── style.py            # "Night Mint" koyu tema (QSS)
├── center/
│   ├── main_window.py      # Kenar çubuklu ana pencere
│   ├── page_dashboard.py   # Genel bakış / istatistikler
│   ├── page_products.py    # Ürün CRUD (koli barkodu dahil)
│   ├── page_stock.py       # Stok çubuk grafiği (QPainter)
│   ├── page_dealers.py     # Bayi CRUD
│   └── page_reports.py     # Tarih/bayi filtreli satış raporları
└── pos/
    ├── main_window.py      # POS ekranı (sepet, ödeme)
    └── barcode_camera.py   # Kamera ile okuma (isteğe bağlı)
```

## Veritabanı Şeması

- **products:** `barcode` (tekil), `name`, `price`, `vat`, `stock`, `box_barcode`, `box_quantity`
- **dealers:** `code` (tekil), `name`, `address`, `phone`
- **sales:** `dealer_code`, `date`, `payment_type`, `total`, `items[]`

Eski Türkçe koleksiyon/alan adlarıyla kaydedilmiş veriler, uygulama ilk
bağlandığında otomatik olarak İngilizce şemaya taşınır (veri kaybı olmaz).
