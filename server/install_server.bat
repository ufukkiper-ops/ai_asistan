@echo off
REM KipGPT - kole PC sunucu kurulumu (Windows)
cd /d "%~dp0\.."
setlocal EnableDelayedExpansion

echo ========================================
echo   KipGPT Kole Sunucu Kurulumu
echo ========================================
echo.

REM 1) Python / venv
py -3 --version >nul 2>&1
if errorlevel 1 (
  echo [HATA] Python 3 yok. https://www.python.org/downloads/
  echo Kurarken "Add python.exe to PATH" isaretleyin.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] Sanal ortam olusturuluyor...
  py -3 -m venv .venv
) else (
  echo [1/5] Sanal ortam hazir.
)

call .venv\Scripts\activate.bat
echo [2/5] Bagimliliklar kuruluyor...
pip install -q -r requirements.txt
pip install -q waitress

REM 2) .env
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo [3/5] .env olusturuldu — duzenleyin: FLASK_SECRET_KEY, OPENAI_API_KEY
) else (
  echo [3/5] .env mevcut.
)

REM 3) Firewall (admin gerekir)
echo [4/5] Windows Guvenlik Duvari kurali (port 5001)...
net session >nul 2>&1
if errorlevel 1 (
  echo   UYARI: Yonetici degilsiniz. Firewall icin bu dosyayi "Yonetici olarak calistir".
) else (
  netsh advfirewall firewall delete rule name="KipGPT Server" >nul 2>&1
  netsh advfirewall firewall add rule name="KipGPT Server" dir=in action=allow protocol=TCP localport=5001 >nul
  echo   Port 5001 izin verildi.
)

REM 4) Otomatik baslatma (Task Scheduler)
echo [5/5] Windows acilista otomatik baslatma...
set "RUN_BAT=%~dp0run_server.bat"
set "TASK_NAME=KipGPTServer"

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

schtasks /Create /TN "%TASK_NAME%" /TR "\"%RUN_BAT%\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
if errorlevel 1 (
  echo   Gorev olusturulamadi. Elle: Gorev Zamanlayici -^> KipGPTServer
) else (
  echo   Gorev olusturuldu: %TASK_NAME% (oturum acilinca)
)

echo.
echo ========================================
echo   Kurulum tamam.
echo.
echo   1) .env dosyasini doldurun
echo   2) server\run_server.bat calistirin
echo   3) Telefon / diger PC: http://BU-PC-IP:5001
echo.
echo   IP ogrenmek: ipconfig
echo   Uyku kapali tutun: Guc secenekleri -^> Uykuya gecme: Hicbir zaman
echo ========================================
pause
endlocal
