@echo off
title TruthLens Server
cd /d "%~dp0"

set "PYTHON=C:\Users\ROG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%PYTHON%" (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON=py"
)

if not exist "%PYTHON%" (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON=python"
)

echo.
echo  TruthLens is starting...
echo  Open http://127.0.0.1:8000 in your browser.
echo.
echo  IMPORTANT: Keep this window open while using the app.
echo  Press Ctrl+C to stop the server.
echo.

"%PYTHON%" app.py

echo.
echo TruthLens stopped. If an error appeared above, take a screenshot of it.
pause
