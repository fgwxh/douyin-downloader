@echo off

REM Start Douyin Downloader UI
REM Author: Douyin Downloader
REM Date: 2026-02-24

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Start server in a new window
start "Douyin Downloader Server" cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8501 --workers 1"

REM Wait for server to start
echo Starting server, please wait...
timeout /t 5 /nobreak >nul

REM Start browser
echo Starting browser...
start http://localhost:8501/frontend

REM Wait for user input
echo Server started. Press any key to stop the server and exit.
echo.
pause

REM Stop the server
REM Find and stop the uvicorn process
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Stop the server window
taskkill /F /FI "WINDOWTITLE eq Douyin Downloader Server" >nul 2>&1

echo Server stopped. Exiting...
timeout /t 2 /nobreak >nul
