# Exe Derleme Rehberi

Yazar Kasa uygulamalarını (merkez + kasa) standalone exe dosyalarına dönüştürme.

## Hızlı Başlangıç

### Linux / macOS
```bash
cd ~/Desktop/yazarkasa
./build_all.sh
```

### Windows
```cmd
cd \Users\USERNAME\Desktop\yazarkasa
build_all.bat
```

Oluşan exe'ler: `dist/yazarkasa-merkez(.exe)` ve `dist/yazarkasa-kasa(.exe)`

---

## Bireysel Derleme

### Sadece Merkez
```bash
./build_center.sh       # Linux/macOS
build_center.bat        # Windows
```

### Sadece Kasa
```bash
./build_pos.sh          # Linux/macOS
build_pos.bat           # Windows
```

---

## Teknik Detaylar

- **PyInstaller**: Exe'ler yönetici olmadan çalışır
- **Derleme Süresi**: Merkez 3-5 dk, Kasa 2-3 dk (sistem hızına göre)
- **Exe Boyutu**: ~120 MB (PyQt5 + MongoDB driver + Qt plugin'ler)
- **Antivirus**: İlk çalıştırmada uyarı gelirse → "İzin Ver" / "Çalıştır"
- **Kurulum**: Yapılmaz — exe direkt çalıştırılır
- **Kaldırma**: exe'leri sil, bitti

---

## Dağıtım İçin Paketleme

Kuruluma dağıtılacak dosyalar:

```
yazarkasa-dist/
  ├─ yazarkasa-merkez(.exe)       ← merkez exe
  ├─ yazarkasa-kasa(.exe)         ← kasa exe  
  ├─ config.json                  ← ayarlar (MongoDB URI buradan)
  ├─ KURULUM.txt                  ← basit adımlar
  └─ README.md                    ← sistem bilgisi
```

### Kurulum Yapısı (Son Kullanıcı Bilgisayarı)

1. Dizin oluştur: `C:\Program Files\Yazarkasa` (Windows)
2. exe + config.json kopyala
3. config.json'da `mongo_uri` ayarla (merkez sunucusu veya cloud)
4. `yazarkasa-merkez.exe` çalıştır (ürün/bayi ayarlarını yap)
5. `yazarkasa-kasa.exe` çalıştır (kasada satış başla)

---

## MongoDB Başlatma (Exe Çalıştırmadan Önce)

**Podman ile**:
```bash
podman start yazarkasa-mongo
```

**Windows sistemi kurulu MongoDB**:
- Otomatik başlar (sistem servisi)

**Cloud (MongoDB Atlas)**:
- İnternet bağlantısı yeterli

---

## Sorun Giderme

### "config.json bulunamadı" hatası
→ Exe'yle aynı dizine config.json kopyala

### "MongoDB bağlanamadı" hatası
→ MongoDB başladığından ve mongo_uri doğru olduğundan emin ol

### Exe başlamıyor
→ Terminal'de direkt çalıştır (hata mesajını gör)
```bash
./dist/yazarkasa-merkez
```

### "DLL import error" (Windows)
→ Visual C++ redistributable kurlu: https://support.microsoft.com/en-us/help/2977003/

---

## Notlar

- Exe'ler Python kurulumu gerektirmez (bağımlılıklar içine yazılı)
- config.json sisteme özel değildir (başka bilgisayara taşınabilir)
- Ürün/bayi verileri MongoDB'de; exe'ler sadece UI
