@echo off
REM KipGPT - GitHub'dan guncelle + sunucuyu yeniden baslat
cd /d "%~dp0\.."
setlocal

echo ========================================
echo   KipGPT Guncelleme
echo ========================================
echo.

REM Calisan sunucu varsa kapat (port 5001 / waitress / app.py)
echo [1/4] Eski sunucu durduruluyor...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo [2/4] GitHub'dan cekiliyor (git pull)...
git fetch origin
git pull
if errorlevel 1 (
  echo.
  echo [HATA] git pull basarisiz. Internet / branch kontrol edin.
  pause
  exit /b 1
)

echo [3/4] Bagimliliklar guncelleniyor...
if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
  pip install -q -r requirements.txt
  pip install -q waitress
) else (
  echo [.venv yok] Once server\install_server.bat calistirin.
  pause
  exit /b 1
)

echo [4/4] Sunucu baslatiliyor...
echo.
start "KipGPT Server" cmd /k "%~dp0run_server.bat"

echo.
echo Tamam. Yeni pencerede sunucu acildi.
echo Diger cihazlar: http://BU-PC-IP:5001
timeout /t 4 >nul
endlocal
