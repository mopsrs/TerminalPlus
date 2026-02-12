# MOPS Terminal

A modern, feature-rich terminal emulator for Windows built with PyQt5. Designed for developers and power users who want a sleek alternative to the standard Windows Command Prompt.

## Features

**Core Features**
- Clean, dark-themed GUI with syntax highlighting
- Support for all Windows CMD and PowerShell commands
- Command history with arrow key navigation
- Intelligent command autocomplete
- Built-in utility commands for common tasks
- Lightweight and responsive

**Advanced Features**
- **Multi-window support** - Open multiple independent terminal instances
- **Split view mode** - Dual panes for side-by-side reference/logging
- **Command favorites** - Save and reuse frequently used commands
- **HTTP server** - Quick development server for testing
- **Archive extraction** - Built-in support for ZIP and TAR files
- **WiFi profile manager** - View saved WiFi networks and passwords
- **Mathematical expressions** - Evaluate calculations without external tools

## Requirements

- **Python 3.6+** or higher
- **PyQt5** - GUI framework
- **Windows OS** - Optimized for Windows (some features Windows-specific)

## Installation

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mops-terminal.git
   cd mops-terminal
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the terminal**
   ```bash
   python mops_terminal.py
   ```

### Auto-Startup Configuration

To launch MOPS Terminal automatically on Windows startup:

1. Right-click `install_startup.bat` and select "Run as administrator"
2. The script creates a shortcut in your Windows Startup folder
3. Restart your computer - the terminal launches automatically

For detailed setup instructions, see [STARTUP_README.txt](STARTUP_README.txt)

## Usage

### Command Categories

#### Navigation & Filesystem
| Command | Description |
|---------|-------------|
| `pwd` | Display current working directory |
| `cd [path]` | Change directory |
| `ls` / `dir` | List directory contents |
| `mkdir [dir]` | Create new directory |
| `tree [path]` | Display directory tree structure |
| `copy [src] [dst]` | Copy files |
| `del [file]` | Delete files |
| `type [file]` | Display file contents |

#### System Information
| Command | Description |
|---------|-------------|
| `whoami` | Display current user |
| `systeminfo` | Show system information |
| `ipconfig` | Display network configuration |
| `tasklist` | List running processes |

#### Development Utilities
| Command | Description |
|---------|-------------|
| `calc [expr]` | Evaluate mathematical expressions |
| `serve [port]` | Start HTTP server (default: 8000) |
| `stopserve` | Stop running server |
| `mops install [pkg]` | Install Python packages via pip |
| `wifcode [--show]` | List saved WiFi networks |
| `extract [archive]` | Extract ZIP or TAR archives |
| `search [pattern]` | Search text in files |
| `mkcd [dir]` | Create directory and change into it |

#### Terminal Features (New!)
| Command | Description |
|---------|-------------|
| `newwindow` | Open new terminal window |
| `splitview` | Toggle split view (dual pane) |
| `favorite [cmd]` | Add command to favorites |
| `favorites` | List all saved favorites |
| `help` / `?` | Display command reference |
| `clear` / `cls` | Clear terminal screen |
| `exit` | Close terminal |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **↑ / ↓ Arrows** | Navigate command history |
| **Tab** | Autocomplete commands or filenames |
| **Enter** | Execute command |

### Examples

**Open a second terminal window:**
```
> newwindow
✓ New terminal window opened.
```

**Enable split view for dual panes:**
```
> splitview
✓ Split view enabled! Use secondary pane for reference.
```

**Save a frequently used command:**
```
> favorite dir /s /b
✓ Added to favorites: dir /s /b
```

**View all saved favorites:**
```
> favorites
━━━━━━━━━━ Favorite Commands ━━━━━━━━━━
  dir                  → dir /s /b
  python               → python -m http.server 8000
```

**Start a local development server:**
```
> serve 3000
Serving C:\Users\mops\project at http://localhost:3000/ (pid 12345)
```

## Project Structure

```
mops-terminal/
├── mops_terminal.py              Main application
├── launch_mops_terminal.bat       Launcher script
├── install_startup.bat            Auto-startup installer
├── requirements.txt               Python dependencies
├── README.md                      Documentation
├── LICENSE                        MIT License
└── STARTUP_README.txt             Startup guide
```

## Building Standalone Executable

To create a single executable for distribution:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed -i icon.ico mops_terminal.py
```

The compiled executable will be located in the `dist/` directory.

## Configuration

### Favorite Commands

Favorite commands are stored in `~/.mops_favorites.json` and persist across sessions:

```json
{
  "dir": "dir /s /b",
  "server": "python -m http.server 8000",
  "python": "python --version"
}
```

## Troubleshooting

### Administrator Privileges

Some commands require admin privileges. For full functionality:
- Right-click the terminal shortcut → "Run as administrator"
- Commands affected: `wifcode`, `ipconfig`, `tasklist`

### Module Not Found Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Character Encoding Issues

On older Windows systems, set console encoding:
```bash
chcp 65001
```

## Contributing

Contributions are welcome! Please:
- Report bugs via GitHub Issues
- Submit pull requests with improvements
- Suggest new features and enhancements
- Test on Windows 10/11

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created and maintained by **MOPS**

## Support

For issues, questions, or feature requests:
- Open a GitHub Issue
- Check existing documentation
- Review the STARTUP_README.txt for setup issues

---

**Enjoy using MOPS Terminal!** 🚀
