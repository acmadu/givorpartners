#!/bin/bash
# Tüm uygulamaları exe olarak derle (merkez + kasa)

set -e
cd "$(dirname "$0")"

echo "🔨 YAZARKASA — Tüm Uygulamalar Derleniyor..."
echo ""

# Merkez
./build_center.sh
echo ""

# Kasa
./build_pos.sh
echo ""

echo "✅ HER İKİ UYGULAMA DERLENDI!"
echo ""
echo "Dağıtım klasörü: dist/"
echo "  • yazarkasa-merkez (merkez yönetim)"
echo "  • yazarkasa-kasa   (satış kasası)"
echo ""
echo "⚠️  İlk çalıştırmada antivirus uyarısı gelirse normal — imzasız exe olduğu için."
