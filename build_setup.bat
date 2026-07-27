@echo off
REM GivorPartners — Windows Installer Olusturma (Inno Setup)
REM Oncesinde: build_center.bat ve build_pos.bat calistirilmali

cd /d "%~dp0"

echo.
echo ========================================
echo  GivorPartners Setup Dosyalari Olusturuluyor
echo ========================================
echo.

REM 1. Exe'ler derle
echo [1/3] Exe derlemeleri baslatiliyor...
call build_all.bat
if %errorlevel% neq 0 (
    echo [HATA] Exe derleme basarısız!
    pause
    exit /b 1
)

echo.
echo [2/3] Setup dosyalari olusturuluyor...
echo.
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Inno Setup Compiler (iscc.exe) bulunamadi!
    echo.
    echo Inno Setup 6 yukle: https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

REM dist/ klasoru kontrol et
if not exist dist\yazarkasa-merkez.exe (
    echo [HATA] dist\yazarkasa-merkez.exe bulunamadi!
    echo Oncesinde: build_center.bat
    pause
    exit /b 1
)

if not exist dist\yazarkasa-kasa.exe (
    echo [HATA] dist\yazarkasa-kasa.exe bulunamadi!
    echo Oncesinde: build_pos.bat
    pause
    exit /b 1
)

REM config.json.example kontrol et
if not exist config.json.example (
    echo [HATA] config.json.example bulunamadi!
    pause
    exit /b 1
)

REM Output klasorunu temizle
if exist installer\Output rmdir /s /q installer\Output
mkdir installer\Output

echo [2/3] Merkez Setup Dosyasi Olusturuluyor...
echo        yazarkasa-merkez-setup.iss
iscc "installer\yazarkasa-merkez-setup.iss"
if %errorlevel% neq 0 (
    echo [HATA] Merkez setup olusturulamadi!
    pause
    exit /b 1
)

echo.
echo [3/3] Kasa (POS) Setup Dosyasi Olusturuluyor...
echo        yazarkasa-kasa-setup.iss
iscc "installer\yazarkasa-kasa-setup.iss"
if %errorlevel% neq 0 (
    echo [HATA] Kasa setup olusturulamadi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ✓ Tamamlandi!
echo ========================================
echo.
echo Olusturulan Dosyalar:
echo   1. installer\Output\yazarkasa-merkez-setup-v1.0.0.exe
echo   2. installer\Output\yazarkasa-kasa-setup-v1.0.0.exe
echo.
echo MERKEZ YONETICILERINE GONDER:
echo   → yazarkasa-merkez-setup-v1.0.0.exe
echo.
echo BAYILERE GONDER:
echo   → yazarkasa-kasa-setup-v1.0.0.exe
echo.
echo BAYİ KURULUMU:
echo   1. yazarkasa-kasa-setup-v1.0.0.exe'yi cift tikla
echo   2. NEXT, NEXT, INSTALL
echo   3. Sezon'da otomatik baslar
echo.
pause
pause
