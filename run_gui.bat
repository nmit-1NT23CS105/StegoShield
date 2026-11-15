@echo off
title StegoShield
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (python gui.py) else (py gui.py)
if errorlevel 1 pause
