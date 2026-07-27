@echo off
setlocal DisableDelayedExpansion
REM GivorPartners - Windows Installer Olusturma (Inno Setup)

cd /d "%~dp0"

echo.
echo ========================================
echo  GivorPartners Setup Dosyalari Olusturuluyor
echo ========================================
echo.

where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Inno Setup bulunamadi.
    echo Inno Setup 6 yukle: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

if not exist dist\yazarkasa-merkez.exe (
    echo [HATA] dist\yazarkasa-merkez.exe bulunamadi.
    pause
    exit /b 1
)

if not exist dist\yazarkasa-kasa.exe (
    echo [HATA] dist\yazarkasa-kasa.exe bulunamadi.
    pause
    exit /b 1
)

if exist installer\Output rmdir /s /q installer\Output
mkdir installer\Output

echo.
echo Kurulum yapilandan once config.json hazirlaniyor...
python setup_config.py
if %errorlevel% neq 0 (
    echo [HATA] config.json olusturulamadi
    pause
    exit /b 1
)

echo [1/2] Merkez Setup olusturuluyor...
iscc "installer\yazarkasa-merkez-setup.iss"
if %errorlevel% neq 0 (
    echo [HATA] Merkez setup olusturulamadi.
    pause
    exit /b 1
)

echo [2/2] Kasa Setup olusturuluyor...
iscc "installer\yazarkasa-kasa-setup.iss"
if %errorlevel% neq 0 (
    echo [HATA] Kasa setup olusturulamadi.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  TAMAMLANDI
echo ========================================
echo   installer\Output\yazarkasa-merkez-setup-v1.0.0.exe
echo   installer\Output\yazarkasa-kasa-setup-v1.0.0.exe
echo.
