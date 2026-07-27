@echo off
REM Kasa (POS) uygulamasini exe olarak derle (Windows) — spec dosyasi kullanir

cd /d "%~dp0"

echo.
echo Kasa (POS) Uygulamasi Derleniyor (Windows)...

for /f "tokens=*" %%i in ('pyinstaller --version') do set PYVER=%%i
echo    PyInstaller surumu: %PYVER%

REM Gerekli paketleri yukle
echo Gerekli paketler yukleniyor...
pip install PyQt5 PyQtChart pymongo openpyxl pyinstaller --quiet

REM Eski build dosyalarini temizle
if exist build\yazarkasa-kasa rmdir /s /q build\yazarkasa-kasa

REM Spec dosyasiyla derle
pyinstaller yazarkasa-kasa.spec

echo.
echo Tamamlandi!
echo    Exe dosyasi: dist\yazarkasa-kasa.exe
echo.
pause
