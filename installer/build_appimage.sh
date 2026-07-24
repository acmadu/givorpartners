#!/bin/bash
# ============================================================
#  GivorPartners — Linux AppImage Oluşturucu
#  Gereksinim: appimagetool (otomatik indirilir)
#  Kullanım: ./installer/build_appimage.sh [merkez|kasa|her ikisi]
# ============================================================
set -e
cd "$(dirname "$0")/.."   # Proje köküne geç

TARGET="${1:-her ikisi}"

# ── appimagetool indir (yoksa) ────────────────────────────
APPIMAGETOOL="./installer/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "appimagetool indiriliyor..."
    curl -L -o "$APPIMAGETOOL" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

VERSION=$(python3 -c "import version; print(version.VERSION)" 2>/dev/null || echo "1.0.0")

# ── AppDir hazırlama fonksiyonu ──────────────────────────
build_appdir() {
    local APP_NAME="$1"        # givorpartners-kasa veya givorpartners-merkez
    local EXE_SRC="$2"         # dist/yazarkasa-kasa  veya dist/yazarkasa-merkez
    local DISPLAY_NAME="$3"    # GivorPartners Kasa   veya GivorPartners Merkez

    local APPDIR="installer/AppDir-${APP_NAME}"

    echo ""
    echo "▶ ${DISPLAY_NAME} AppImage oluşturuluyor..."

    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

    # Exe kopyala
    cp "$EXE_SRC" "$APPDIR/usr/bin/${APP_NAME}"
    chmod +x "$APPDIR/usr/bin/${APP_NAME}"

    # config.json varsa kopyala (yok ise oluştur)
    if [ -f "config.json" ]; then
        cp "config.json" "$APPDIR/usr/bin/config.json"
    fi

    # .desktop dosyası
    cat > "$APPDIR/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Name=${DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Type=Application
Categories=Office;Finance;
Comment=GivorPartners Bayi Yönetim Sistemi
EOF
    cp "$APPDIR/${APP_NAME}.desktop" "$APPDIR/usr/share/applications/"

    # İkon (varsa assets/icon.png, yoksa boş PNG oluştur)
    if [ -f "assets/icon.png" ]; then
        cp "assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
        cp "assets/icon.png" "$APPDIR/${APP_NAME}.png"
    else
        # Basit yer tutucu PNG
        python3 -c "
import struct, zlib
def make_png(w=256,h=256,r=42,g=80,b=120):
    def chunk(t,d): c=zlib.crc32(t+d)&0xffffffff; return struct.pack('>I',len(d))+t+d+struct.pack('>I',c)
    img=b''.join(b'\x00'+bytes([r,g,b,255]*w) for _ in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(img))+chunk(b'IEND',b'')
open('${APPDIR}/${APP_NAME}.png','wb').write(make_png())
"
        cp "$APPDIR/${APP_NAME}.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
    fi

    # AppRun — başlatıcı
    cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/usr/bin:$PATH"
cd "$APPDIR/usr/bin"
exec "$APPDIR/usr/bin/__APPNAME__" "$@"
APPRUN
    sed -i "s/__APPNAME__/${APP_NAME}/g" "$APPDIR/AppRun"
    chmod +x "$APPDIR/AppRun"

    # AppImage oluştur
    ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "installer/${APP_NAME}-v${VERSION}.AppImage" 2>&1
    chmod +x "installer/${APP_NAME}-v${VERSION}.AppImage"

    echo "✅ Oluşturuldu: installer/${APP_NAME}-v${VERSION}.AppImage"
}

# ── Derleme ──────────────────────────────────────────────
case "$TARGET" in
    kasa)
        build_appdir "givorpartners-kasa" "dist/yazarkasa-kasa" "GivorPartners Kasa"
        ;;
    merkez)
        build_appdir "givorpartners-merkez" "dist/yazarkasa-merkez" "GivorPartners Merkez"
        ;;
    *)
        build_appdir "givorpartners-kasa" "dist/yazarkasa-kasa" "GivorPartners Kasa"
        build_appdir "givorpartners-merkez" "dist/yazarkasa-merkez" "GivorPartners Merkez"
        ;;
esac

echo ""
echo "════════════════════════════════════"
echo "AppImage dosyaları: installer/*.AppImage"
echo "Çalıştırma: chmod +x givorpartners-kasa-*.AppImage && ./givorpartners-kasa-*.AppImage"
echo "════════════════════════════════════"
