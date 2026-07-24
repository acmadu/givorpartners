@echo off
REM Tüm uygulamaları exe olarak derle (Windows)

cd /d "%~dp0"

echo.
echo 🔨 YAZARKASA — Tüm Uygulamalar Derleniyor (Windows)...
echo.

call build_center.bat
if errorlevel 1 goto error

call build_pos.bat
if errorlevel 1 goto error

echo.
echo ✅ HER İKİ UYGULAMA DERLENDI!
echo.
echo Dağıtım klasörü: dist\
echo   • yazarkasa-merkez.exe  (merkez yönetim)
echo   • yazarkasa-kasa.exe    (satış kasası)
echo.
echo ⚠️  İlk çalıştırmada antivirus uyarısı gelirse normal — imzasız exe olduğu için.
echo.
pause
goto end

:error
echo.
echo ❌ DERLEME HATASI!
pause
:end
