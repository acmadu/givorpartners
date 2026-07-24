#!/bin/bash
# Kasa (POS) uygulamasını exe olarak derle — spec dosyası kullanır

set -e
cd "$(dirname "$0")"

echo "🔨 Kasa (POS) Uygulaması Derleniyor..."
echo "   PyInstaller sürümü: $(pyinstaller --version)"

# Eski build dosyalarını temizle
rm -rf build/yazarkasa-kasa

# Spec dosyasıyla derle
pyinstaller yazarkasa-kasa.spec

echo "✅ Tamamlandı!"
echo "   📦 Exe dosyası: dist/yazarkasa-kasa  (Linux/macOS)"
echo "              veya dist/yazarkasa-kasa.exe  (Windows)"
