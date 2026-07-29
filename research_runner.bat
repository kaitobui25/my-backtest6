@echo off
setlocal EnableExtensions EnableDelayedExpansion
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
echo ============================================================
echo Chay tat ca config YAML trong folder - TRAIN
echo ============================================================
echo.
echo Vi du:
echo   config\v0.9
echo.
set "CONFIG_DIR="
set /p "CONFIG_DIR=Nhap folder config: "
set "CONFIG_DIR=%CONFIG_DIR:"=%"

if not defined CONFIG_DIR (
    echo Folder rong.
    pause
    goto :MENU
)

if not exist "%CONFIG_DIR%\" (
    echo Khong tim thay folder: %CONFIG_DIR%
    pause
    goto :MENU
)

set /a CONFIG_COUNT=0
for /r "%CONFIG_DIR%" %%F in (search_*.yaml search_*.yml) do (
    if exist "%%~fF" set /a CONFIG_COUNT+=1
)

if "%CONFIG_COUNT%"=="0" (
    echo Khong tim thay search_*.yaml hoac search_*.yml trong:
    echo   %CONFIG_DIR%
    pause
    goto :MENU
)

echo.
echo Tim thay %CONFIG_COUNT% config:
for /r "%CONFIG_DIR%" %%F in (search_*.yaml search_*.yml) do (
    if exist "%%~fF" echo   %%~fF
)
echo.
set "CONFIRM="
set /p "CONFIRM=Chay tat ca tren TRAIN? [Y/n]: "
if /i "%CONFIRM%"=="n" goto :MENU

set /a CURRENT=0
for /r "%CONFIG_DIR%" %%F in (search_*.yaml search_*.yml) do (
    if exist "%%~fF" (
        set /a CURRENT+=1
        echo.
        echo ============================================================
        echo [!CURRENT!/%CONFIG_COUNT%] %%~fF
        echo ============================================================

        "%PYTHON%" -m exactbt.cli search --config "%%~fF" --split train
        set "RUN_EXIT=!ERRORLEVEL!"

        if not "!RUN_EXIT!"=="0" (
            echo.
            echo [ERROR] Config failed with exit code !RUN_EXIT!:
            echo   %%~fF
            echo.
            echo Batch stopped. Checkpoint da hoan thanh van duoc giu lai.
            pause
            exit /b !RUN_EXIT!
        )
    )
)

echo.
echo ============================================================
echo Da chay xong %CONFIG_COUNT% config trong folder:
echo   %CONFIG_DIR%
echo ============================================================
echo.
pause
exit /b 0
