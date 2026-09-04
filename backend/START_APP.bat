@echo off
setlocal

title STARZ - Order Automation System

echo.
echo ================================================
echo   STARZ - ORDER AUTOMATION SYSTEM
echo ================================================
echo.

REM =================================================
REM 1. Se placer dans le dossier du fichier BAT
REM =================================================

cd /d "%~dp0"

echo Dossier application :
echo %CD%
echo.


REM =================================================
REM 2. Detecter Python
REM =================================================

set "PYTHON_CMD="

where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=py"
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [ERREUR] Python n'est pas installe sur ce PC.
    echo.
    echo Installez Python puis relancez START_APP.bat.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detecte.
echo.


REM =================================================
REM 3. Creer le virtual environment si necessaire
REM =================================================

if not exist "venv\Scripts\python.exe" (

    echo Creation de l'environnement Python...
    echo.

    %PYTHON_CMD% -m venv venv

    if errorlevel 1 (
        echo.
        echo [ERREUR] Impossible de creer l'environnement Python.
        pause
        exit /b 1
    )

    echo [OK] Environnement Python cree.
    echo.
)


REM =================================================
REM 4. Installer / mettre a jour les dependances
REM =================================================

echo Verification des dependances Python...
echo.

"venv\Scripts\python.exe" -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo [ERREUR] Echec de la mise a jour de pip.
    pause
    exit /b 1
)

"venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible d'installer les dependances.
    pause
    exit /b 1
)

echo.
echo [OK] Dependances Python disponibles.
echo.


REM =================================================
REM 5. Detecter Tesseract OCR
REM =================================================

set "TESSERACT_EXE="

REM Tesseract dans le PATH
where tesseract >nul 2>&1

if %errorlevel%==0 (
    for /f "delims=" %%i in ('where tesseract') do (
        if not defined TESSERACT_EXE (
            set "TESSERACT_EXE=%%i"
        )
    )
)

REM Installation Windows standard
if not defined TESSERACT_EXE (
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        set "TESSERACT_EXE=C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
)

REM Installation Windows 32 bits
if not defined TESSERACT_EXE (
    if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
        set "TESSERACT_EXE=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    )
)


REM =================================================
REM 6. Bloquer si Tesseract absent
REM =================================================

if not defined TESSERACT_EXE (

    echo.
    echo ================================================
    echo   TESSERACT OCR NON INSTALLE
    echo ================================================
    echo.
    echo L'application peut lire les PDF texte,
    echo mais les PDF scannes necessitent Tesseract OCR.
    echo.
    echo Installez Tesseract avec :
    echo.
    echo winget install --id tesseract-ocr.tesseract -e
    echo.
    echo Puis relancez START_APP.bat.
    echo.

    pause
    exit /b 1
)


REM =================================================
REM 7. Fournir le chemin Tesseract a Python
REM =================================================

set "TESSERACT_CMD=%TESSERACT_EXE%"

echo [OK] Tesseract OCR detecte :
echo %TESSERACT_EXE%
echo.


REM =================================================
REM 8. Verifier les imports Python essentiels
REM =================================================

echo Verification OCR...
echo.

"venv\Scripts\python.exe" -c "import streamlit, openpyxl, pypdf, pytesseract, pymupdf, PIL; print('[OK] Modules Python valides.')"

if errorlevel 1 (
    echo.
    echo [ERREUR] Une dependance Python est manquante.
    echo.
    pause
    exit /b 1
)

echo.


REM =================================================
REM 9. Verifier le BLOG RJ45
REM =================================================

if not exist "data\input\BLOG 2026 - Rj45_cleaned.xlsx" (

    echo.
    echo ================================================
    echo   BLOG RJ45 INTROUVABLE
    echo ================================================
    echo.
    echo Placez le fichier :
    echo.
    echo BLOG 2026 - Rj45_cleaned.xlsx
    echo.
    echo dans :
    echo.
    echo %CD%\data\input
    echo.
    pause
    exit /b 1
)

echo [OK] BLOG RJ45 detecte.
echo.


REM =================================================
REM 10. Lancer Streamlit
REM =================================================

echo ================================================
echo   LANCEMENT DE L'APPLICATION
echo ================================================
echo.
echo Le navigateur va s'ouvrir automatiquement.
echo.
echo Pour fermer l'application :
echo Ctrl + C
echo.

"venv\Scripts\python.exe" -m streamlit run streamlit_app.py

echo.
echo Application fermee.
pause