@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    py -3.12 -m venv .venv
    if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import duckdb; from PySide6 import QtWidgets" >nul 2>&1
if errorlevel 1 (
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto fail
)
.venv\Scripts\python.exe desktop.py
if errorlevel 1 goto fail
exit /b 0
:fail
pause
exit /b 1
