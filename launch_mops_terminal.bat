@echo off
REM Launch MOPS Terminal on Windows startup with high priority
setlocal enabledelayedexpansion

REM Get the directory of this batch file
set SCRIPT_DIR=%~dp0

REM Activate venv if it exists
if exist "%SCRIPT_DIR%..\..\venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%..\..\venv\Scripts\activate.bat"
)

REM Launch the Python script with high priority (-high priority class)
cd /d "%SCRIPT_DIR%"
start "MOPSR Terminal" /HIGH pythonw.exe mops_terminal.py

exit /b 0
