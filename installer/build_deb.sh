#!/bin/bash
# ============================================================
#  GivorPartners — Linux .deb Paketi Oluşturucu (Debian/Ubuntu)
#  Kullanım: ./installer/build_deb.sh [kasa|merkez|her ikisi]
# ============================================================
set -e
cd "$(dirname "$0")/.."

TARGET="${1:-her ikisi}"
VERSION=$(python3 -c "import version; print(version.VERSION)" 2>/dev/null || echo "1.0.0")
ARCH="amd64"

build_deb() {
    local APP_NAME="$1"          # givorpartners-kasa
    local EXE_SRC="$2"          # dist/yazarkasa-kasa
    local DISPLAY_NAME="$3"     # GivorPartners Kasa
    local DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}"
    local PKGDIR="installer/deb/${DEB_NAME}"

    echo ""
    echo "▶ ${DISPLAY_NAME} .deb paketi oluşturuluyor..."

    rm -rf "$PKGDIR"
    mkdir -p \
        "$PKGDIR/DEBIAN" \
        "$PKGDIR/usr/bin" \
        "$PKGDIR/usr/share/applications" \
        "$PKGDIR/usr/share/icons/hicolor/256x256/apps" \
        "$PKGDIR/usr/share/doc/${APP_NAME}"

    # Exe
    cp "$EXE_SRC" "$PKGDIR/usr/bin/${APP_NAME}"
    chmod +x "$PKGDIR/usr/bin/${APP_NAME}"

    # config.json → /etc/givorpartners (ilk kurulumda, var ise üzerine yazma)
    mkdir -p "$PKGDIR/etc/givorpartners"
    if [ -f "config.json" ]; then
        cp "config.json" "$PKGDIR/etc/givorpartners/config.json"
    fi

    # .desktop
    cat > "$PKGDIR/usr/share/applications/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Name=${DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Type=Application
Categories=Office;Finance;
Comment=GivorPartners Bayi Yönetim Sistemi
EOF

    # İkon
    if [ -f "assets/icon.png" ]; then
        cp "assets/icon.png" "$PKGDIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    fi

    # DEBIAN/control
    INSTALLED_KB=$(du -sk "$EXE_SRC" | awk '{print $1}')
    cat > "$PKGDIR/DEBIAN/control" <<EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: misc
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_KB}
Maintainer: GivorPartners <destek@givorpartners.com>
Description: GivorPartners Bayi Yönetim Sistemi
 ${DISPLAY_NAME} — Bayi satış ve yönetim platformu.
EOF

    # DEBIAN/conffiles — config.json upgrade'de korunsun
    echo "/etc/givorpartners/config.json" > "$PKGDIR/DEBIAN/conffiles"

    # DEBIAN/postinst — exe config.json için /etc'ye bak
    cat > "$PKGDIR/DEBIAN/postinst" <<'POSTINST'
#!/bin/bash
set -e
echo "GivorPartners kurulumu tamamlandı."
POSTINST
    chmod 755 "$PKGDIR/DEBIAN/postinst"

    # Paketle
    dpkg-deb --build --root-owner-group "$PKGDIR" "installer/${DEB_NAME}.deb"
    echo "✅ Oluşturuldu: installer/${DEB_NAME}.deb"
    echo "   Kurulum: sudo dpkg -i installer/${DEB_NAME}.deb"
    echo "   Güncelleme: sudo dpkg -i installer/${DEB_NAME}.deb  (aynı komut)"
    echo "   Kaldırma: sudo apt remove ${APP_NAME}"
}

case "$TARGET" in
    kasa)
        build_deb "givorpartners-kasa" "dist/yazarkasa-kasa" "GivorPartners Kasa"
        ;;
    merkez)
        build_deb "givorpartners-merkez" "dist/yazarkasa-merkez" "GivorPartners Merkez"
        ;;
    *)
        build_deb "givorpartners-kasa" "dist/yazarkasa-kasa" "GivorPartners Kasa"
        build_deb "givorpartners-merkez" "dist/yazarkasa-merkez" "GivorPartners Merkez"
        ;;
esac

echo ""
echo "════════════════════════════════════"
echo ".deb dosyaları: installer/deb/*.deb"
echo "════════════════════════════════════"
