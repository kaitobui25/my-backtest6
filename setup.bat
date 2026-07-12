@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
endlocal
