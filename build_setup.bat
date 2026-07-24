@echo off
REM Build setup.exe using Inno Setup
REM Windows'ta çalıştır: build_setup.bat

cd /d "%~dp0"

REM 1. Exe'ler derle
echo [1/2] Exe derlemesini başlat...
call build_all.bat
if errorlevel 1 (
    echo Exe derleme başarısız!
    pause
    exit /b 1
)

REM 2. Inno Setup ile setup.exe oluştur
echo [2/2] Setup.exe oluşturuluyor...

REM Inno Setup's default installation path
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\iscc.exe"

if not exist %INNO_SETUP% (
    echo.
    echo ❌ Inno Setup bulunamadı!
    echo.
    echo Lütfen Inno Setup 6'yı indir ve kur:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo Ardından build_setup.bat'i tekrar çalıştır.
    pause
    exit /b 1
)

REM Compile setup.iss
%INNO_SETUP% "installer\yazarkasa-setup.iss"
if errorlevel 1 (
    echo Setup.exe derleme başarısız!
    pause
    exit /b 1
)

echo.
echo ✅ Tamamlandı!
echo.
echo Setup dosyası: installer\Output\GivorPartners-Setup.exe
echo.
echo Bayi'ye gönderecek dosyalar:
echo   📦 installer\Output\GivorPartners-Setup.exe
echo   📄 config.json
echo.
pause
