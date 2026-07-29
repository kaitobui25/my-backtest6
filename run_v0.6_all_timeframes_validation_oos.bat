@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "PYTHONPATH=%CD%\src"
set "RESULT_ROOT=results\v0.6_timeframes"
set "STATUS_LOG=%RESULT_ROOT%\run_validation_oos_status.log"
set "HELPER=scripts\run_v06_all_timeframe_splits.py"

if not exist "%PYTHON%" (
    echo [ERROR] Virtual environment not found: %PYTHON%
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "src\exactbt\cli.py" (
    echo [ERROR] ExactBT source package not found: %CD%\src\exactbt
    echo.
    pause
    exit /b 1
)

if not exist "%HELPER%" (
    echo [ERROR] Helper not found: %HELPER%
    echo.
    pause
    exit /b 1
)

"%PYTHON%" -c "import exactbt, exactbt.cli, pandas" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python cannot import ExactBT or pandas.
    echo Python    : %CD%\%PYTHON%
    echo PYTHONPATH: %PYTHONPATH%
    echo.
    pause
    exit /b 1
)

if not exist "%RESULT_ROOT%" mkdir "%RESULT_ROOT%"

>"%STATUS_LOG%" echo ExactBT v0.6 all-timeframe VALIDATION and FINAL OOS
>>"%STATUS_LOG%" echo Started: %DATE% %TIME%
>>"%STATUS_LOG%" echo Python: %CD%\%PYTHON%
>>"%STATUS_LOG%" echo PYTHONPATH: %PYTHONPATH%

cls
echo ============================================================
echo ExactBT v0.6 - ALL BTC TIMEFRAMES
echo VALIDATION first, then locked FINAL OOS
echo ============================================================
echo.
echo Timeframes:
echo   M5  M15  M30  H1  H2  H4
echo.
echo Rules:
echo   TRAIN passing_results  -^> VALIDATION
echo   VALIDATION passing_results -^> FINAL OOS
echo   Zero-passing timeframes are logged and skipped.
echo   Completed checkpoints are reused on rerun.
echo.
echo Status log:
echo   %CD%\%STATUS_LOG%
echo.

call :RUN_PHASE validation
if errorlevel 1 goto :FAILED

echo.
echo ============================================================
echo ALL VALIDATION RUNS ARE FINISHED
echo ============================================================
echo.
echo FINAL OOS is locked.
echo The BAT will use only passing_results from VALIDATION.
echo Do not change YAML, thresholds, grids, or shortlist now.
echo.
set "OOS_CONFIRM="
set /p "OOS_CONFIRM=Type OOS to unlock and run FINAL OOS for all timeframes: "
if /I not "%OOS_CONFIRM%"=="OOS" goto :VALIDATION_ONLY

>>"%STATUS_LOG%" echo FINAL OOS unlocked: %DATE% %TIME%
call :RUN_PHASE final_oos
if errorlevel 1 goto :FAILED

>>"%STATUS_LOG%" echo Finished successfully: %DATE% %TIME%
echo.
echo ============================================================
echo VALIDATION AND FINAL OOS FINISHED SUCCESSFULLY
echo Results: %CD%\%RESULT_ROOT%
echo Status : %CD%\%STATUS_LOG%
echo ============================================================
echo.
pause
exit /b 0

:RUN_PHASE
set "PHASE=%~1"
echo.
echo ============================================================
echo Running phase: %PHASE%
echo ============================================================
"%PYTHON%" "%HELPER%" "%PHASE%" --status-log "%STATUS_LOG%"
exit /b %ERRORLEVEL%

:VALIDATION_ONLY
>>"%STATUS_LOG%" echo FINAL OOS not unlocked: %DATE% %TIME%
echo.
echo ============================================================
echo VALIDATION FINISHED. FINAL OOS WAS NOT UNLOCKED.
echo Run this BAT again when ready; validation checkpoints resume.
echo Status: %CD%\%STATUS_LOG%
echo ============================================================
echo.
pause
exit /b 0

:FAILED
set "FINAL_EXIT=%ERRORLEVEL%"
>>"%STATUS_LOG%" echo Batch failed code=%FINAL_EXIT%: %DATE% %TIME%
echo.
echo ============================================================
echo BATCH STOPPED BECAUSE A TIMEFRAME FAILED
echo Exit code: %FINAL_EXIT%
echo Check the error above and:
echo   %CD%\%STATUS_LOG%
echo.
echo Completed ExactBT checkpoints are preserved.
echo Run this BAT again to resume.
echo ============================================================
echo.
pause
exit /b %FINAL_EXIT%
