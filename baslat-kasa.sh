#!/bin/bash
# ============================================================
#  GivorPartners Kasa (POS) — Linux Hızlı Başlat
#  MongoDB'yi otomatik başlatır ve exe açar
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXE_PATH="$SCRIPT_DIR/dist/yazarkasa-kasa"

if [ ! -f "$EXE_PATH" ]; then
    echo ""
    echo "✗ HATA: yazarkasa-kasa bulunamadı"
    echo "  Beklenen: $EXE_PATH"
    echo ""
    echo "  Çözüm:"
    echo "  1. ./build_all.sh çalıştır (exe derler)"
    echo "  2. Tekrar ./baslat-kasa.sh çalıştır"
    echo ""
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║   GivorPartners Kasa — Başlatılıyor        ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# MongoDB'yi kontrol et ve başlat
echo "⏳ MongoDB kontrol ediliyor..."

# Podman kontayneri
if command -v podman &>/dev/null; then
    STATE=$(podman ps --filter "name=yazarkasa-mongo" --format "{{.State}}" 2>/dev/null)
    if [ "$STATE" = "running" ]; then
        echo "   • Podman yazarkasa-mongo çalışıyor ✓"
    else
        echo "   • Podman kontayneri başlatılıyor..."
        if podman start yazarkasa-mongo 2>/dev/null; then
            echo "   • Kontayner başlatıldı ✓"
            sleep 2
        else
            echo "   ⚠ Kontayner başlatılamadı"
        fi
    fi
elif command -v sudo &>/dev/null && sudo systemctl is-active --quiet mongod 2>/dev/null; then
    # Systemd mongod
    echo "   • Systemd mongod çalışıyor ✓"
elif command -v sudo &>/dev/null; then
    # systemd mongod başlatmaya çalış
    echo "   • MongoDB başlatılıyor (systemd)..."
    if sudo systemctl start mongod 2>/dev/null; then
        echo "   • MongoDB başlatıldı ✓"
        sleep 2
    else
        echo "   ⚠ MongoDB başlatılamadı"
        echo "   Çözüm: sudo systemctl start mongod"
    fi
else
    echo "   ⚠ MongoDB başlatılamadı — manual kontrol et"
fi

echo ""
echo "🚀 GivorPartners Kasa açılıyor..."
echo ""

# exe'yi çalıştır (arka planda)
"$EXE_PATH" &

echo "✓ Uygulama başlatıldı"
echo ""
echo "İPUÇ: Giriş bilgileri:"
echo "  Bayi: bayi1"
echo "  Şifre: 123456"
echo ""
