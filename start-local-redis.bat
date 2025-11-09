@echo off
echo ========================================
echo YouTube Downloader with Redis - Local
echo ========================================
echo.

REM Check if Redis is accessible
echo Checking Redis connection...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis is not running!
    echo.
    echo Please start Redis first:
    echo   - Using WSL: wsl sudo service redis-server start
    echo   - Using Docker: docker run -d -p 6379:6379 redis:7-alpine
    echo.
    pause
    exit /b 1
)
echo [OK] Redis is running
echo.

REM Set environment variables
set REDIS_HOST=localhost
set REDIS_PORT=6379
set MAX_PARALLEL_DOWNLOADS=3
set CORS_ORIGINS=http://localhost:3000

REM Start backend
echo Starting Backend...
cd backend
start "YT-DLP Backend" cmd /k "python main.py"
timeout /t 3 >nul
echo [OK] Backend started
echo.

REM Start frontend
echo Starting Frontend...
cd ..\frontend
echo REACT_APP_API_URL=http://localhost:8000 > .env.development
start "YT-DLP Frontend" cmd /k "npm start"
echo [OK] Frontend starting...
echo.

echo ========================================
echo Application URLs:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
echo Configuration:
echo   Redis: localhost:6379
echo   Max Parallel: 3 downloads
echo.
echo Test Batch Downloads:
echo   1. Open http://localhost:3000
echo   2. Click "Batch Download"
echo   3. Add 3-5 YouTube URLs
echo   4. Watch parallel downloads!
echo ========================================
echo.
echo Press any key to stop all services...
pause >nul

echo.
echo Stopping services...
taskkill /FI "WindowTitle eq YT-DLP Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq YT-DLP Frontend*" /T /F >nul 2>&1
echo Done!