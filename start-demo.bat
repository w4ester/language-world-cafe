@echo off
cls
echo ================================================================
echo  Cafe Language Learning - AI Demo Startup
echo ================================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] Ollama not found!
    echo.
    echo Please install Ollama from: https://ollama.com/download/windows
    echo.
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Start Ollama service
echo [*] Starting Ollama service...
start /B ollama serve > nul 2>&1
timeout /t 3 /nobreak > nul

REM Check for Qwen3:14B model
echo [*] Checking for Qwen3:14B model...
ollama list | findstr /C:"qwen3:14b" > nul
if errorlevel 1 (
    echo [!] Qwen3:14B not found. Downloading ^(9.3GB^)...
    echo     This will take 5-10 minutes
    echo.
    ollama pull qwen3:14b
    if errorlevel 1 (
        echo [X] Failed to download Qwen3:14B
        pause
        exit /b 1
    )
)
echo [OK] Qwen3:14B ready!

REM Check Python dependencies
echo [*] Checking Python dependencies...
python -c "import flask, faster_whisper, ollama" 2>nul
if errorlevel 1 (
    echo [!] Installing Python dependencies...
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        echo     Try manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies installed!

echo.
echo ================================================================
echo  All systems ready!
echo ================================================================
echo.

REM Start backend service
echo [*] Starting AI backend service ^(Flask + Whisper + Qwen3^)...
start /B python backend_service.py > nul 2>&1
timeout /t 3 /nobreak > nul
echo [OK] Backend running

REM Start HTTP server
echo [*] Starting HTTP server for frontend...
start /B python -m http.server 8000 > nul 2>&1
timeout /t 2 /nobreak > nul
echo [OK] HTTP server running

echo.
echo ================================================================
echo  Demo is ready!
echo ================================================================
echo.
echo  Frontend:  http://localhost:8000
echo  Backend:   http://localhost:5000
echo  AI Model:  Qwen3:14B ^(119 languages^)
echo  Speech:    Whisper ^(medium^)
echo.
echo  Opening demo in browser...
echo.

REM Open browser
start http://localhost:8000/ai-chat-demo.html

echo ================================================================
echo  Demo is running!
echo.
echo  Press any key to stop all services
echo ================================================================
echo.

pause

echo.
echo ================================================================
echo  Shutting down demo...
echo ================================================================
echo.

REM Kill Python processes on ports 5000 and 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /F /PID %%a > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a > nul 2>&1

echo [OK] All services stopped
echo.
echo Thanks for using the demo!
echo.
pause
