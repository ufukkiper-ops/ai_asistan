@echo off
REM KipGPT - surekli acik sunucu (Windows)
cd /d "%~dp0\.."
setlocal EnableDelayedExpansion

if not exist ".venv\Scripts\python.exe" (
  echo [.venv yok] Olusturuluyor...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Python bulunamadi. https://www.python.org/downloads/ adresinden kurun.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
pip install -q waitress

if not exist ".env" (
  if exist ".env.example" copy ".env.example" ".env" >nul
  echo [.env olusturuldu] FLASK_SECRET_KEY ve OPENAI_API_KEY doldurun.
)

REM Yerel ag IP
set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set "CAND=%%a"
  set "CAND=!CAND: =!"
  if not "!CAND!"=="127.0.0.1" if "!LAN_IP!"=="" set "LAN_IP=!CAND!"
)

if "%LAN_IP%"=="" (
  set "PUBLIC_BASE_URL=http://127.0.0.1:5001"
) else (
  set "PUBLIC_BASE_URL=http://!LAN_IP!:5001"
)

set "PORT=5001"
set "RENDER="
set "RAILWAY="

echo ========================================
echo   KipGPT SUNUCU
echo   Bu PC:     http://127.0.0.1:5001
if not "%LAN_IP%"=="" echo   Ag:       http://%LAN_IP%:5001
echo   Health:    http://127.0.0.1:5001/health
echo ========================================
echo   Bu pencereyi KAPATMAYIN. Sunucu burada calisir.
echo.

python -c "from waitress import serve; from app import app; print('Waitress dinliyor...'); serve(app, host='0.0.0.0', port=5001, threads=8)"
pause
endlocal
