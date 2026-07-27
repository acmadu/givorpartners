@echo off
REM Merkez yonetim uygulamasini exe olarak derle (Windows) — spec dosyasi kullanir

cd /d "%~dp0"

echo.
echo Merkez Yonetim Uygulamasi Derleniyor (Windows)...

for /f "tokens=*" %%i in ('pyinstaller --version') do set PYVER=%%i
echo    PyInstaller surumu: %PYVER%

REM Gerekli paketleri yukle
echo Gerekli paketler yukleniyor...
pip install PyQt5 PyQtChart pymongo openpyxl pyinstaller --quiet

REM Eski build dosyalarini temizle
if exist build\yazarkasa-merkez rmdir /s /q build\yazarkasa-merkez

REM Spec dosyasiyla derle
pyinstaller yazarkasa-merkez.spec

echo.
echo Tamamlandi!
echo    Exe dosyasi: dist\yazarkasa-merkez.exe
echo.
pause
