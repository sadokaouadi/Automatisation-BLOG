@echo off
cd /d "%~dp0"
title Order Copilot AI - Manager Test

echo ============================================
echo        ORDER COPILOT AI - MANAGER TEST
echo ============================================
echo.

REM ------------------------------------------------
REM Rechercher Python
REM ------------------------------------------------

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
    echo.
    echo ERREUR : Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python puis relancer ce fichier.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------
REM Creer le venv au premier lancement
REM ------------------------------------------------

if not exist "venv\Scripts\python.exe" (

    echo [1/3] Creation de l'environnement Python...
    %PYTHON_CMD% -m venv venv

    if errorlevel 1 (
        echo.
        echo ERREUR lors de la creation du venv.
        pause
        exit /b 1
    )

    echo.
    echo [2/3] Installation des bibliotheques...
    "venv\Scripts\python.exe" -m pip install --upgrade pip
    "venv\Scripts\python.exe" -m pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo ERREUR lors de l'installation des bibliotheques.
        pause
        exit /b 1
    )

) else (

    echo [1/3] Environnement Python deja installe.
    echo [2/3] Bibliotheques deja installees.

)

REM ------------------------------------------------
REM Lancer Streamlit
REM ------------------------------------------------

echo.
echo [3/3] Lancement de l'application...
echo.
echo Ne fermez pas cette fenetre pendant l'utilisation.
echo.

"venv\Scripts\python.exe" -m streamlit run streamlit_app.py

echo.
echo Application fermee.
pause
