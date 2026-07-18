@echo off
REM ============================================================================
REM FPL Bill Extractor — One-Click Launcher for Windows
REM ============================================================================
REM Double-click this file. It will set up and launch the GUI.
REM
REM Prerequisites (install once manually):
REM   1. Python: https://www.python.org/downloads/ (check "Add to PATH")
REM   2. Tesseract: https://github.com/UB-Mannheim/tesseract/wiki (add to PATH)
REM   3. Poppler: https://github.com/osbo/poppler-windows/releases (add bin/ to PATH)
REM   4. Git: https://git-scm.com/download/win
REM ============================================================================

cd /d "%~dp0"

echo.
echo ======================================
echo   FPL Bill Extractor - Setup
echo ======================================
echo.

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Install from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo [OK] Python found

REM Check tesseract
where tesseract >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Tesseract not found - scanned bill OCR will not work.
    echo Install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Digital PDFs will still work fine.
    echo.
)

REM Create venv if needed
if not exist ".venv" (
    echo [SETUP] Creating Python environment...
    python -m venv .venv
)

REM Activate
call .venv\Scripts\activate.bat

REM Install deps if needed
if not exist ".venv\.deps_installed" (
    echo [SETUP] Installing Python libraries...
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    echo. > .venv\.deps_installed
)

echo.
echo Launching FPL Bill Extractor...
echo.
python gui.py
