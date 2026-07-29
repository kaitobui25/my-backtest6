@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

rem Dam bao package src\exactbt duoc tim thay ke ca khi editable install bi mat sau git pull/merge.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

".venv\Scripts\python.exe" "scripts\research_runner.py"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" echo Runner exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
