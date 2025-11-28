@echo off
echo ========================================
echo   ScentCraft Print Agent Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install httpx click python-dateutil --quiet

echo [2/3] Dependencies installed!
echo.

REM Check for .env file or prompt for API key
if exist ".env" (
    echo [3/3] Found .env file, starting agent...
    python agent.py
) else (
    echo [3/3] No .env file found.
    echo.
    echo Please enter your API key (get it from the URL below):
    echo https://printserver-production.up.railway.app/api/dev/printer-api-key/b1070uv-brooklyn
    echo.
    set /p API_KEY="API Key: "
    echo.
    echo Starting agent...
    python agent.py --api-url https://printserver-production.up.railway.app --api-key %API_KEY% --queue-dir "C:\ScentCraftQueue"
)

pause

