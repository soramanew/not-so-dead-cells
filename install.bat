@echo off

setlocal

:: Check if python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo "Python >= 3.12 is required"
    exit /b 1
)

:: Check python version
for /f "delims=" %%i in ('python -c "import sys; print(sys.version_info.minor >= 12)"') do set version_check=%%i
if "%version_check%" == "False" (
    echo "Python >= 3.12 is required"
    exit /b 1
)

:: Change to script dir
cd /d "%~dp0" || exit /b 1

:: Check if git is installed and update repo
where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    git pull origin main
)

:: Create venv
python3 -m venv .venv
:: Activate venv
.venv\Scripts\activate
:: Install deps
pip install -r requirements.txt
:: Package
pip install -U pyinstaller
pyinstaller --noconfirm main.spec

:: Rename executable
ren dist\main\main.exe "Not so Dead Cells.exe"

endlocal
