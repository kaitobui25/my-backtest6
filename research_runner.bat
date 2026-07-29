@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Virtual environment not found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

rem Dam bao package src\exactbt duoc tim thay ke ca khi editable install bi mat sau git pull/merge.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

:MENU
cls
echo ============================================================
echo ExactBT Research Runner
echo ============================================================
echo.
echo [1] Chon 1 config / TRAIN - VALIDATION - FINAL OOS
echo [2] Chon folder config va chay tat ca YAML tren TRAIN
echo [0] Thoat
echo.
set "MODE="
set /p "MODE=Lua chon: "

if "%MODE%"=="0" exit /b 0
if "%MODE%"=="1" goto :INTERACTIVE
if "%MODE%"=="2" goto :RUN_FOLDER

echo Lua chon khong hop le.
pause
goto :MENU

:INTERACTIVE
"%PYTHON%" "scripts\research_runner.py"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" echo Runner exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

:RUN_FOLDER
cls
"%PYTHON%" "scripts\run_config_folder.py"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" echo Folder runner exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
