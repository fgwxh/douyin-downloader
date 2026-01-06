@echo off

REM Start Douyin Downloader UI
REM Author: Douyin Downloader
REM Date: 2026-01-06

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo Starting Douyin Downloader UI...
echo Please wait, this may take a few seconds...
echo.
echo After startup, you can access the UI through the following links:
echo - Local access: http://localhost:8522
echo - Network access: http://[your-local-ip]:8522
echo.

REM Start Streamlit application with browser open disabled
start /b python -m streamlit run app.py --browser.gatherUsageStats false --server.port 8522 --server.headless true

REM Wait for server to start
echo Starting server, please wait...
timeout /t 5 /nobreak >nul

REM Start browser only if not already opened by Streamlit
echo Starting browser...
start http://localhost:8522

REM Wait for user input
pause