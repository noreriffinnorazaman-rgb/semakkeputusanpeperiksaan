@echo off
cd /d "%~dp0"

:: Auto-detect IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%

echo ============================================
echo   SISTEM DAPA 2026
echo   SMK TUANKU LAILATUL SHAHREEN
echo ============================================
echo.
echo Starting server...
echo.
echo Buka browser dan taip:
echo.
echo   http://localhost:5000
echo.
echo Guru-guru lain boleh taip:
echo.
echo   http://%LOCAL_IP%:5000
echo.
echo Jangan tutup window ini selagi sistem digunakan.
echo Tekan Ctrl+C untuk hentikan sistem.
echo ============================================
echo.
python app.py
pause
