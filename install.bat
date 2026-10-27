@echo off
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
    echo.
    echo L'installation a echoue. Consultez le message ci-dessus.
    pause
    exit /b 1
)

echo.
echo Installation terminee. Le raccourci STARZ Order Manager est sur le Bureau.
pause
