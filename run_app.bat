@echo off
title StegoShield Web App
cd /d "%~dp0"

rem ---- find Python (python, or the py launcher)
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (
    where py >nul 2>nul && set "PY=py"
)
if not defined PY (
    echo Python was not found. Install Python 3.10+ from python.org
    echo and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

rem ---- install packages only if something is missing
%PY% -c "import flask, PIL, numpy, cryptography, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo Installing required packages, please wait...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Package install failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

echo.
echo  StegoShield is starting at http://127.0.0.1:5000
echo  Keep this window open while you use the app. Close it to stop.
echo.
rem open the browser after a short delay so the server is ready
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"
%PY% app.py
if errorlevel 1 pause
