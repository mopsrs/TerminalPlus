MOPSR Terminal - Auto-Startup Installation
============================================

To make MOPSR Terminal launch automatically when you start your Windows computer:

METHOD 1: Automatic Installation (Recommended)
----------------------------------------------

1. Right-click on "install_startup.bat" in this folder
2. Select "Run as administrator" (IMPORTANT - must be admin!)
3. The script will create a shortcut in your Windows Startup folder
4. Restart your computer - MOPSR Terminal will launch automatically

The terminal will now:
- Launch at startup with HIGH priority (launches before many other apps)
- Appear in fullscreen immediately
- Display the boot menu


METHOD 2: Manual Installation (Alternative)
--------------------------------------------

If the automatic script doesn't work:

1. Press Windows + R to open Run dialog
2. Type: shell:startup
3. This opens your Startup folder
4. Copy "launch_mops_terminal.bat" into this folder
5. Restart your computer


REMOVING AUTO-STARTUP
---------------------

If you want to disable auto-startup:

1. Press Windows + R
2. Type: shell:startup
3. Find and delete "MOPSR Terminal.lnk" or the batch file shortcut
4. Restart your computer

Alternatively, use the Run dialog:
1. Windows + R
2. Type: msconfig
3. Go to "Startup" tab
4. Uncheck "MOPSR Terminal"
5. Click OK and restart


TROUBLESHOOTING
---------------

If the terminal doesn't start:
- Make sure Python and PyQt5 are installed
- Check that the venv is set up correctly
- Run install_startup.bat as Administrator
- Check Windows Startup folder for the shortcut
- Try running launch_mops_terminal.bat manually to test

