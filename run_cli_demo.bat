@echo off
title StegoShield CLI demo
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
echo === 1. HIDE: encrypt + hide a secret in the coffee photo ===
%PY% cli.py hide -i samples\cover_coffee.png -o output\demo_stego.png -m "Operation Nightfall: meet at Gate 2, 9 PM" -p stego123
pause
echo === 2. EXTRACT with the right password ===
%PY% cli.py extract -i output\demo_stego.png -p stego123
echo === 3. EXTRACT with a wrong password ===
%PY% cli.py extract -i output\demo_stego.png -p guess123
pause
echo === 4. DETECT: which photo hides the secret? ===
%PY% cli.py detect -i samples\secret_demo_A.png samples\secret_demo_B.png samples\secret_demo_C.png --investigator "Kataru Rahul Reddy"
echo.
echo Reports are in the output folder.
pause
