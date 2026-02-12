@echo off
REM Add MOPS Terminal to Windows Startup
REM Run this script as Administrator to enable auto-start on boot

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set BATCH_DIR=%~dp0launch_mops_terminal.bat
set BATCH_DIR=%BATCH_DIR:"=%

REM Get the Startup folder path
for /f "tokens=*" %%a in ('powershell -Command "[Environment]::GetFolderPath('Startup')"') do (
    set STARTUP_FOLDER=%%a
)

echo Installing MOPS Terminal to Windows Startup...
echo Batch file: %BATCH_DIR%
echo Startup folder: %STARTUP_FOLDER%

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: This script must be run as Administrator!
    echo Please right-click this script and select "Run as administrator"
    pause
    exit /b 1
)

REM Create a shortcut using PowerShell (more reliable than VBScript)
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\MOPSR Terminal.lnk'); " ^
    "$Shortcut.TargetPath = '%BATCH_DIR%'; " ^
    "$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$Shortcut.Description = 'MOPSR Terminal - Launches on system startup'; " ^
    "$Shortcut.Save()" 

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! MOPS Terminal has been added to Windows Startup.
    echo It will launch automatically when you restart your computer.
    echo.
    echo Shortcut location: %STARTUP_FOLDER%\MOPSR Terminal.lnk
) else (
    echo.
    echo ERROR: Failed to create startup shortcut.
    echo Please try running this script as Administrator.
)

pause
