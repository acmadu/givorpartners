@echo off
REM ============================================================
REM  GivorPartners Kasa (POS) — Windows Hızlı Başlat
REM  MongoDB'yi otomatik başlatır ve exe açar
REM ============================================================

setlocal enabledelayedexpansion

REM Exe yolunu belirle (batch dosyasının konumundan)
set SCRIPT_DIR=%~dp0
set EXE_PATH=%SCRIPT_DIR%dist\yazarkasa-kasa.exe

if not exist "%EXE_PATH%" (
    echo.
    echo ✗ HATA: yazarkasa-kasa.exe bulunamadı
    echo   Beklenen: %EXE_PATH%
    echo.
    echo   Çözüm:
    echo   1. build_all.bat çalıştır (exe derler)
    echo   2. Tekrar bu batch dosyasını çalıştır
    echo.
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════╗
echo ║   GivorPartners Kasa — Başlatılıyor        ║
echo ╚════════════════════════════════════════════╝
echo.

REM MongoDB Services olup olmadığını kontrol et
echo ⏳ MongoDB kontrol ediliyor...
sc query MongoDB >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   • MongoDB servis bulundu
    REM Servis durumunu kontrol et
    for /f "tokens=3" %%a in ('sc query MongoDB ^| find "STATE"') do set MONGO_STATE=%%a
    if "!MONGO_STATE!"=="RUNNING" (
        echo   • MongoDB zaten çalışıyor ✓
    ) else (
        echo   • MongoDB başlatılıyor...
        net start MongoDB >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo   • MongoDB başlatıldı ✓
            timeout /t 2 /nobreak >nul
        ) else (
            echo   ⚠ MongoDB başlatılamadı (izin hatası olabilir)
            echo   Lütfen "yönetici olarak çalıştır" ile deneyiniz
        )
    )
) else (
    echo   ⚠ MongoDB servis yüklü değil
    echo   • Seçenek 1: MongoDB Enterprise yükle
    echo   • Seçenek 2: config.json'da MongoDB Atlas URI kullan
)

echo.
echo 🚀 GivorPartners Kasa açılıyor...
echo.

REM exe'yi çalıştır
start "" "%EXE_PATH%"

echo ✓ Uygulama başlatıldı
echo.
echo İPUÇ: Giriş bilgileri:
echo   Bayi: bayi1
echo   Şifre: 123456
echo.
