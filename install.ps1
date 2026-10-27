param(
    [string]$InstallDirectory = (Join-Path $env:LOCALAPPDATA "Programs\STARZ Order Manager")
)

$ErrorActionPreference = "Stop"

try {
    $sourceDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue

    if (-not $launcher) {
        throw "Python 3 est requis. Installez Python depuis https://www.python.org/downloads/windows/ puis relancez install.bat."
    }

    $versionOutput = & $launcher.Source -3 --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3 est requis. Installez Python depuis https://www.python.org/downloads/windows/ puis relancez install.bat."
    }
    $pythonVersion = [version](($versionOutput -split "\s+")[-1])
    if ($pythonVersion -lt [version]"3.10") {
        throw "Python 3.10 or later is required. Update Python and run install.bat again."
    }

    $excludedDirectories = @(
        (Join-Path $sourceDirectory ".git"),
        (Join-Path $sourceDirectory ".venv"),
        "__pycache__",
        (Join-Path $sourceDirectory "data\database"),
        (Join-Path $sourceDirectory "data\uploads"),
        (Join-Path $sourceDirectory "data\exports")
    )

    & robocopy.exe $sourceDirectory $InstallDirectory /E /R:2 /W:2 /XD $excludedDirectories /XF "*.pyc" ".env"
    if ($LASTEXITCODE -ge 8) {
        throw "La copie des fichiers de l'application a echoue (code robocopy $LASTEXITCODE)."
    }

    $pythonDirectory = Join-Path $InstallDirectory ".venv"
    $pythonExecutable = Join-Path $pythonDirectory "Scripts\python.exe"
    $pythonWindowedExecutable = Join-Path $pythonDirectory "Scripts\pythonw.exe"

    if (-not (Test-Path $pythonExecutable)) {
        & $launcher.Source -3 -m venv $pythonDirectory
        if ($LASTEXITCODE -ne 0) {
            throw "La creation de l'environnement Python a echoue."
        }
    }

    & $pythonExecutable -m pip install -r (Join-Path $InstallDirectory "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "L'installation des dependances a echoue. Verifiez votre connexion Internet puis relancez install.bat."
    }

    & $pythonExecutable -c "import main"
    if ($LASTEXITCODE -ne 0) {
        throw "La verification de l'application a echoue."
    }

    $desktopDirectory = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopDirectory "STARZ Order Manager.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pythonWindowedExecutable
    $shortcut.Arguments = '"main.py"'
    $shortcut.WorkingDirectory = $InstallDirectory
    $shortcut.IconLocation = (Join-Path $InstallDirectory "assets\starz.ico") + ",0"
    $shortcut.Description = "Lancer STARZ Order Manager"
    $shortcut.Save()
}
catch {
    Write-Error $_
    exit 1
}
