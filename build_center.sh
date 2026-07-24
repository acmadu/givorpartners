#!/bin/bash
# Merkez yönetim uygulamasını exe olarak derle — spec dosyası kullanır

set -e
cd "$(dirname "$0")"

echo "🔨 Merkez Yönetim Uygulaması Derleniyor..."
echo "   PyInstaller sürümü: $(pyinstaller --version)"

# Eski build dosyalarını temizle
rm -rf build/yazarkasa-merkez

# Spec dosyasıyla derle
pyinstaller yazarkasa-merkez.spec

echo "✅ Tamamlandı!"
echo "   📦 Exe dosyası: dist/yazarkasa-merkez  (Linux/macOS)"
echo "              veya dist/yazarkasa-merkez.exe  (Windows)"
