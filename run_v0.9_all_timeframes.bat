@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "RESULT_ROOT=results\v0.9_timeframes"
set "STATUS_LOG=%RESULT_ROOT%\run_all_status.log"

if not exist "%PYTHON%" (
    echo [ERROR] Khong tim thay Python: %PYTHON%
    echo Hay chay setup.bat truoc.
    pause
    exit /b 1
)

if not exist "%RESULT_ROOT%" mkdir "%RESULT_ROOT%"

> "%STATUS_LOG%" echo ExactBT v0.9 all-timeframe TRAIN run
>>"%STATUS_LOG%" echo Started: %DATE% %TIME%

cls
echo ============================================================
echo ExactBT v0.9 - RUN ALL BTC TIMEFRAMES - TRAIN
echo ============================================================
echo.
echo Ket qua duoc tach rieng tai:
echo   %RESULT_ROOT%\m5
echo   %RESULT_ROOT%\m15
echo   %RESULT_ROOT%\m30
echo   %RESULT_ROOT%\h1
echo   %RESULT_ROOT%\h2
echo   %RESULT_ROOT%\h4
echo.

call :RUN_ONE M5  "config\v0.9\search_v0.9_trend_following_m5.yaml"
if errorlevel 1 goto :FAILED
call :RUN_ONE M15 "config\v0.9\search_v0.9_trend_following_m15.yaml"
if errorlevel 1 goto :FAILED
call :RUN_ONE M30 "config\v0.9\search_v0.9_trend_following_m30.yaml"
if errorlevel 1 goto :FAILED
call :RUN_ONE H1  "config\v0.9\search_v0.9_trend_following_h1.yaml"
if errorlevel 1 goto :FAILED
call :RUN_ONE H2  "config\v0.9\search_v0.9_trend_following_h2.yaml"
if errorlevel 1 goto :FAILED
call :RUN_ONE H4  "config\v0.9\search_v0.9_trend_following_h4.yaml"
if errorlevel 1 goto :FAILED

>>"%STATUS_LOG%" echo Finished successfully: %DATE% %TIME%
echo.
echo ============================================================
echo DA CHAY XONG TAT CA 6 TIMEFRAME
echo Results: %CD%\%RESULT_ROOT%
echo Status : %CD%\%STATUS_LOG%
echo ============================================================
pause
exit /b 0

:RUN_ONE
set "TIMEFRAME=%~1"
set "CONFIG_FILE=%~2"

if not exist "%CONFIG_FILE%" (
    echo [ERROR] Khong tim thay config: %CONFIG_FILE%
    >>"%STATUS_LOG%" echo FAILED %TIMEFRAME% - config not found - %DATE% %TIME%
    exit /b 2
)

echo.
echo ------------------------------------------------------------
echo Dang chay %TIMEFRAME%
echo Config: %CONFIG_FILE%
echo ------------------------------------------------------------
>>"%STATUS_LOG%" echo START %TIMEFRAME% - %DATE% %TIME%

"%PYTHON%" -m exactbt.cli search --config "%CONFIG_FILE%" --split train
set "RUN_EXIT=%ERRORLEVEL%"

if not "%RUN_EXIT%"=="0" (
    echo [ERROR] %TIMEFRAME% loi, exit code %RUN_EXIT%.
    >>"%STATUS_LOG%" echo FAILED %TIMEFRAME% code=%RUN_EXIT% - %DATE% %TIME%
    exit /b %RUN_EXIT%
)

>>"%STATUS_LOG%" echo DONE %TIMEFRAME% - %DATE% %TIME%
echo Da xong %TIMEFRAME%.
exit /b 0

:FAILED
set "FINAL_EXIT=%ERRORLEVEL%"
>>"%STATUS_LOG%" echo Batch stopped code=%FINAL_EXIT% - %DATE% %TIME%
echo.
echo ============================================================
echo BATCH DUNG VI MOT TIMEFRAME BI LOI
echo Exit code: %FINAL_EXIT%
echo Xem log: %CD%\%STATUS_LOG%
echo Co the chay lai BAT de resume checkpoint da luu.
echo ============================================================
pause
exit /b %FINAL_EXIT%
