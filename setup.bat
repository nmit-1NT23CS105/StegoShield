@echo off
title StegoShield setup
cd /d "%~dp0"
echo ============================================
echo   StegoShield - installing Python packages
echo ============================================
where python >nul 2>nul
if %errorlevel%==0 (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
) else (
    echo "python" not found, trying the "py" launcher...
    py -m pip install --upgrade pip
    py -m pip install -r requirements.txt
)
echo.
echo Done. Double-click run_app.bat to start StegoShield in your browser.
pause
