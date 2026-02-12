<<<<<<< HEAD
# MOPSR Terminal

A sleek, custom terminal emulator for Windows built with PyQt5. Features a boot menu, command history, autocomplete, and various utility commands.

## Features

- 🎨 **Dark Theme UI** - GitHub-inspired dark aesthetic with syntax highlighting
- 🚀 **Boot Menu** - Custom startup sequence with menu selection
- 📜 **Command History** - Navigate through previous commands with arrow keys
- 🔍 **Autocomplete** - Smart tab completion for commands and files
- 🛠️ **Built-in Commands**:
  - File operations (cd, ls, mkdir, del, copy, type, tree)
  - System info (pwd, whoami, systeminfo, ipconfig)
  - Utilities (calc, search, extract archives, serve HTTP)
  - Package management (mops install)
  - WiFi password retrieval (wifcode)
- 🔌 **Windows Integration** - Execute PowerShell and cmd commands
- ✨ **Animated Text** - Smooth character-by-character text animation

## Requirements

- Python 3.6+
- PyQt5
- Windows OS (some commands are Windows-specific)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mops-terminal.git
cd mops-terminal
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Terminal
```bash
python mops_terminal.py
```

## Auto-Startup on Windows

To make MOPSR Terminal launch automatically when you start your computer:

1. Right-click `install_startup.bat` and select "Run as administrator"
2. The script will create a shortcut in your Windows Startup folder
3. Restart your computer - the terminal will launch automatically

See `STARTUP_README.txt` for more details.

## Usage

### Boot Menu
When you first launch the terminal, you'll see a boot menu. Select "Launch Terminal" to proceed.

### Available Commands

#### Navigation & System
- `pwd` - Show current directory
- `cd [path]` - Change directory
- `ls` / `dir` - List directory contents
- `cls` / `clear` - Clear terminal

#### System Information
- `whoami` - Show current user
- `systeminfo` - Display system information
- `ipconfig` - Show network configuration
- `tasklist` - List running processes

#### File Operations
- `copy [src] [dst]` - Copy files
- `del [file]` - Delete files
- `mkdir [dir]` - Create directory
- `type [file]` - Show file content
- `tree [path]` - Show directory tree

#### Utilities
- `search [pattern]` - Search text in files
- `mkcd [dir]` - Create directory and CD into it
- `extract [archive]` - Extract zip/tar archives
- `serve [port]` - Start HTTP server (default 8000)
- `stopserve` - Stop running server
- `mops install [pkg]` - Install Python package
- `wifcode [--show]` - List WiFi profiles (passwords hidden by default)
- `calc [expr]` - Evaluate math expressions

#### Control
- `help` / `?` - Show help menu
- `exit` - Close terminal

### Keyboard Shortcuts
- **↑/↓ Arrow Keys** - Navigate command history
- **Tab** - Autocomplete command or filename
- **Enter** - Execute command

## Project Structure

```
mops-terminal/
├── mops_terminal.py           # Main application
├── launch_mops_terminal.bat    # Startup launcher script
├── install_startup.bat         # Auto-startup installer
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
└── STARTUP_README.txt          # Startup setup instructions
```

## Building for Distribution

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed -i icon.ico mops_terminal.py
```

The executable will be in the `dist/` folder.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs as GitHub issues
- Submit pull requests with improvements
- Suggest new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created with ❤️ by MOPS

## Disclaimer

Some commands (like `wifcode`) require administrator privileges on Windows. Run the terminal as administrator for full functionality.

---

**Have fun with MOPSR Terminal!** 🚀
=======
# TerminalPlus
Passionproject. This might have bugs and not get as much attention.
>>>>>>> c21fb0f8a29560dc6d8972dd91045e2d7a10c4e8
