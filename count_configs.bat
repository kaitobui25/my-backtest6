@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run setup.bat first.
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python scripts\count_configs.py config\search.yaml
endlocal
