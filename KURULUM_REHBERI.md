# GivorPartners — Bayi Kurulum Rehberi
**Sürüm:** 1.0.0 | **Tarih:** 2026-07-26

---

## 📦 Yanınızda Götürülecek Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `yazarkasa-kasa.exe` | Kasa (POS) programı |
| `yazarkasa-merkez.exe` | Merkez yönetim programı (merkez için) |
| `config.json` | Bağlantı ayarları (her bayi için ayrı düzenlenir) |

> **İndirme:** https://github.com/acmadu/givorpartners/releases/latest

---

## 💻 Sistem Gereksinimleri

- Windows 10 / 11 (64-bit)
- İnternet bağlantısı (MongoDB Atlas bulut DB için)
- Ekran çözünürlüğü: minimum 1280×720

---

## 🚀 Kurulum Adımları (Bayi Bilgisayarına)

### 1. Klasör Oluştur

Masaüstünde yeni bir klasör aç:
```
C:\GivorPartners\
```

### 2. Dosyaları Kopyala

USB'den şu dosyaları `C:\GivorPartners\` klasörüne kopyala:
- `yazarkasa-kasa.exe`
- `config.json`

### 3. config.json Düzenle (ÖNEMLİ)

`config.json` dosyasını Not Defteri ile aç ve şu alanları değiştir:

```json
{
  "dealer_code": "BAYI-001",    ← Bayinin kodu (BAYI-002, BAYI-003 vb.)
  "dealer_name": "Bayi Adı",   ← Bayinin gerçek adı
  ...
}
```

> ⚠️ **Dikkat:** `mongo_uri` satırını değiştirme! İnternet bağlantısı olan her cihazda otomatik çalışır.

### 4. Kısayol Oluştur

`yazarkasa-kasa.exe` dosyasına sağ tık → **"Masaüstüne kısayol gönder"**

### 5. İlk Giriş

Kasayı aç → Bayi kullanıcı adı ve şifre ile giriş yap:

| Alan | Değer |
|------|-------|
| Kullanıcı Adı | (Merkezden alınır) |
| Şifre | (Merkezden alınır) |

---

## 🔐 MongoDB Bağlantısı

**Otomatik bağlanır — hiçbir şey kurmanıza gerek yok!**

Program açıldığında internet üzerinden otomatik olarak merkezi veritabanına (MongoDB Atlas) bağlanır. İnternet olduğu sürece her şey çalışır.

> **IP Whitelist:** MongoDB Atlas'ta IP whitelist tüm halkaya açıktır (0.0.0.0/0), her bilgisayardan bağlantı yapılabilir.

---

## 🪟 Windows Kurulum Notları

### Antivirus Uyarısı
Windows Defender veya antivirus yazılımı `.exe` dosyalarını bloklayabilir.

**Çözüm:**
1. `yazarkasa-kasa.exe` üzerine sağ tık
2. **"Yine de çalıştır"** seçeneğini seç
3. Programın bir kez çalıştırılmasını izin ver
4. İkinci kez açılışında sorun olmayacak

### SSL Sertifikaları
Windows'un built-in Microsoft sertifikaları MongoDB Atlas bağlantısını otomatik sağlar. Ek kurulum gerekmez.

### Python Gerekmez
Exe dosyası tamamen bağımsız çalışır, Python yüklü olması gerekmez.

---

## ️ Barkod Okuyucu Bağlantısı

1. Barkod okuyucuyu USB portuna tak
2. Ek sürücü gerekmez (USB HID — tak çalıştır)
3. Kasa açıkken okuyucu otomatik aktif olur

---

## ❗ Sık Karşılaşılan Sorunlar

### Program açılmıyor / Antivirus uyarısı
→ Windows Defender veya antivirüs programı bloklayabilir.
**Çözüm:** `yazarkasa-kasa.exe` dosyasına sağ tık → **"Yine de çalıştır"** seçeneğini seç.

### "Bağlantı hatası" veya "Sunucuya ulaşılamıyor"
→ İnternet bağlantısı yok.
**Çözüm:** İnternet bağlantısını kontrol et, sonra programı yeniden aç.

### Giriş yapılamıyor
→ Kullanıcı adı / şifre hatalı veya hesap tanımlı değil.
**Çözüm:** Merkez yöneticisini ara.

### Ekran küçük / yazılar sığmıyor
→ Program içinden büyütülebilir.
**Çözüm:** Sağ üstteki **"Yazı Boyutu"** butonuna tıkla ve kaydırıcıyı artır.

---

## 📞 Destek

Sorun yaşandığında merkezi ara:
- **Merkez:** _______________
- **Telefon:** _______________

---

## 🔄 Güncelleme

Program her açıldığında otomatik güncelleme kontrol eder. Güncelleme varsa ekranda bildirim gelir → **"Güncelle"** butonuna tıkla.

---

*GivorPartners v1.0.0 — Tüm hakları saklıdır.*
