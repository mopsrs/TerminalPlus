# -*- coding: utf-8 -*-
import sys
import subprocess
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QCompleter, QSplitter
from PyQt5.QtGui import QFont, QColor, QTextCursor, QTextCharFormat
from PyQt5.QtCore import Qt, QSize, QTimer, QStringListModel, QObject, QEvent


class InputKeyFilter(QObject):
    """Event filter for handling QLineEdit key press events properly."""
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.terminal.completer.complete()
                return True
            # Up/down history
            if event.key() == Qt.Key_Up:
                if self.terminal.history_index < len(self.terminal.command_history) - 1:
                    self.terminal.history_index += 1
                    self.terminal.input.setText(self.terminal.command_history[-(self.terminal.history_index + 1)])
                return True
            if event.key() == Qt.Key_Down:
                if self.terminal.history_index > 0:
                    self.terminal.history_index -= 1
                    self.terminal.input.setText(self.terminal.command_history[-(self.terminal.history_index + 1)])
                elif self.terminal.history_index == 0:
                    self.terminal.history_index = -1
                    self.terminal.input.clear()
                return True
        # Pass event through normally for other keys
        return super().eventFilter(obj, event)


class MopsTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.current_dir = os.getcwd()

        # Window setup
        self.setWindowTitle("MOPSR Terminal")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("""
            QWidget { background-color: #0d1117; }
        """)

        # Layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        monospace_font = QFont()
        monospace_font.setFamily("Consolas")
        monospace_font.setPointSize(10)
        self.output.setFont(monospace_font)
        self.output.setStyleSheet("""
            QTextEdit { background-color: #0d1117; color: #c9d1d9; border: none; margin: 0px; }
        """)
        self.layout.addWidget(self.output)

        # Input
        self.input = QLineEdit()
        self.input.setFont(monospace_font)
        self.input.setPlaceholderText("Type a command...")
        self.input.setStyleSheet("""
            QLineEdit { background-color: #1c2128; color: #c9d1d9; border: 2px solid #58a6ff; padding: 8px; }
            QLineEdit:focus { border: 2px solid #79c0ff; }
        """)
        self.layout.addWidget(self.input)
        self.input.returnPressed.connect(self.handle_command)
        
        # Install custom key press handler using event filter
        self._input_filter = InputKeyFilter(self)
        self.input.installEventFilter(self._input_filter)

        # Completer
        self.base_commands = [
            "help", "?", "clear", "cls", "exit", "pwd", "cd", "ls", "dir",
            "whoami", "systeminfo", "ipconfig", "tasklist", "mkdir", "del", "copy",
            "type", "calc", "tree", "open", "echo",
            "search", "mkcd", "extract", "serve", "stopserve", "mops", "mops install", "wifcode"
        ]
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.input.setCompleter(self.completer)
        self.update_completer_model()

        # Server handle
        self.server_process = None

        # Animation helpers
        self._anim_timers = []
        
        # Command favorites
        self.favorites = self.load_favorites()
        
        # Split view toggle
        self.split_view_enabled = False
        self.secondary_output = None
        
        # Show welcome banner
        self.show_welcome()

    # ---------------- UI / Animation ----------------
    def append_text(self, text, color="default", animate=True):
        """Append text to output with specified color and optional animation."""
        color_map = {
            "cyan": "#58a6ff",
            "green": "#3fb950",
            "red": "#f85149",
            "yellow": "#d29922",
            "white": "#c9d1d9",
            "default": "#c9d1d9",
            "gray": "#6e7681",
        }
        html_color = color_map.get(color, color_map["default"])
        
        # If not animating, just insert directly
        if not animate:
            cursor = self.output.textCursor()
            cursor.movePosition(QTextCursor.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(html_color))
            cursor.setCharFormat(fmt)
            cursor.insertText(text)
            self.output.setTextCursor(cursor)
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())
            return
        
        # Animated insertion
        chars_to_insert = list(text)
        index = [0]  # Use list to allow modification in nested function
        
        def insert_next_char():
            if index[0] >= len(chars_to_insert):
                timer.stop()
                try:
                    self._anim_timers.remove(timer)
                except Exception:
                    pass
                return
            
            cursor = self.output.textCursor()
            cursor.movePosition(QTextCursor.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(html_color))
            cursor.setCharFormat(fmt)
            cursor.insertText(chars_to_insert[index[0]])
            self.output.setTextCursor(cursor)
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())
            index[0] += 1
        
        timer = QTimer()
        timer.setInterval(8)  # 8ms per character
        timer.timeout.connect(insert_next_char)
        self._anim_timers.append(timer)
        timer.start()

    def _type_logo(self, logo_text):
        """Display logo text with animation."""
        self.output.clear()
        self.append_text(logo_text, color="white", animate=True)

    # ----------------  Welcome / Startup ----------------

    def show_welcome(self):
        logo = (
"╔════════════════════════════════════════════════════════════════════════════╗\n"
"║                                                                            ║\n"
"║    ███╗   ███╗ ██████╗ ██████╗ ███████╗██████╗ ████████╗███████╗██╗  ██║   ║\n"
"║    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██╔════╝██║  ██║   ║\n"
"║    ██╔████╔██║██║   ██║██████╔╝███████╗██████╔╝   ██║   █████╗  ███████║   ║\n"
"║    ██║╚██╔╝██║██║   ██║██╔═══╝ ╚════██║██╔══██╗   ██║   ██╔══╝  ██╔══██║   ║\n"
"║    ██║ ╚═╝ ██║╚██████╔╝██║     ███████║██║  ██║   ██║   ███████╗██║  ██║   ║\n"
"║    ╚═╝     ╚═╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝   ║\n"
"║                                                                            ║\n"
"║                    Type 'help' to see available commands                   ║\n"
"║                                 Have fun!                                  ║\n"
"╚════════════════════════════════════════════════════════════════════════════╝\n"
        )
        self._type_logo(logo)

    # ---------------- Input handling ----------------
    def handle_command(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.append_text(f"\n> {cmd}\n", color="yellow")
        self.input.clear()

        # Builtin commands
        low = cmd.lower()
        if low in ("help", "?"):
            self.show_help()
        elif low in ("clear", "cls"):
            self.output.clear()
            self.show_welcome()
        elif low == "exit":
            sys.exit(0)
        elif low.startswith("cd "):
            self.change_directory(cmd[3:].strip())
        elif low in ("pwd", "cd"):
            self.append_text(f"{self.current_dir}\n", color="cyan")
        elif low in ("ls", "dir"):
            self.list_dir()
        elif low.startswith("calc "):
            expr = cmd[5:].strip()
            self.calc_expr(expr)
        elif low.startswith("tree"):
            parts = cmd.split()
            path = parts[1] if len(parts) > 1 else self.current_dir
            self.print_tree(path)
        elif low.startswith("wifcode"):
            parts = cmd.split()
            show_flag = len(parts) > 1 and parts[1].lower() in ("--show", "-s", "show")
            self.show_wifi_passwords(show=show_flag)
        elif low.startswith("search "):
            pattern = cmd.split(None, 1)[1]
            self.search_files(pattern)
        elif low.startswith("mkcd "):
            path = cmd.split(None, 1)[1]
            self.make_and_cd(path)
        elif low.startswith("extract "):
            path = cmd.split(None, 1)[1]
            self.extract_archive(path)
        elif low.startswith("serve"):
            parts = cmd.split()
            port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 8000
            self.start_server(port)
        elif low.startswith("stopserve"):
            self.stop_server()
        elif low.startswith("mops "):
            parts = cmd.split()
            pkg = None
            if len(parts) > 2 and parts[1].lower() == "install":
                pkg = parts[2]
            elif len(parts) > 1:
                pkg = parts[1]
            if pkg:
                self.mops_install(pkg)
            else:
                self.append_text("Usage: mops install <package>\n", color="yellow")
        elif low == "newwindow":
            self.open_new_window()
        elif low == "splitview":
            self.toggle_split_view()
        elif low.startswith("favorite "):
            fav_name = cmd.split(None, 1)[1]
            self.add_favorite(fav_name)
        elif low == "favorites":
            self.list_favorites()
        else:
            self.execute_command(cmd)

        # history & completer refresh
        if cmd not in self.command_history:
            self.command_history.append(cmd)
        self.history_index = -1
        self.update_completer_model()

    # ---------------- Filesystem / commands ----------------
    def change_directory(self, path):
        try:
            full_path = os.path.join(self.current_dir, path) if not os.path.isabs(path) else path
            os.chdir(full_path)
            self.current_dir = os.getcwd()
            self.append_text(f"{self.current_dir}\n", color="cyan")
        except FileNotFoundError:
            self.append_text(f"Error: directory is as real as my girlfriend {path}\n", color="red")
        except Exception as e:
            self.append_text(f"Error: {e}\n", color="red")
        finally:
            self.update_completer_model()

    def execute_command(self, cmd):
        try:
            powershell_keywords = ["get-", "set-", "$", "select-object", "where-object", "foreach-object", "invoke-", "test-path", "|"]
            use_powershell = any(k in cmd.lower() for k in powershell_keywords)
            if use_powershell:
                process = subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.current_dir)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, cwd=self.current_dir)
            stdout, stderr = process.communicate()
            if stdout:
                for line in stdout.splitlines():
                    low = line.lower()
                    if "error" in low or "failed" in low:
                        self.append_text(line + "\n", color="red")
                    elif "warning" in low:
                        self.append_text(line + "\n", color="yellow")
                    else:
                        self.append_text(line + "\n", color="white")
            if stderr:
                self.append_text(stderr, color="red")
            if not stdout and not stderr:
                self.append_text("[Command executed]\n", color="gray")
        except Exception as e:
            self.append_text(f"Execution error: {e}\n", color="red")

    # ---------------- Help ----------------
    def show_help(self):
        help_text = """
═══════════════════════════════════════════════════════════════════════════════
                            AVAILABLE COMMANDS
═══════════════════════════════════════════════════════════════════════════════

NAVIGATION & SYSTEM
───────────────────
pwd
  Show current directory
cd [path]
  Change directory
ls / dir
  List directory contents
cls / clear
  Clear terminal

SYSTEM INFORMATION
──────────────────
whoami
  Show current user
systeminfo
  System information
ipconfig
  Show network configuration
tasklist
  List running processes

FILE OPERATIONS
───────────────
copy [src] [dst]
  Copy files
del [file]
  Delete files
mkdir [dir]
  Create directory
type [file]
  Show file content
tree [path]
  Show directory tree

UTILITIES
─────────
search [pattern]
  Search text in files under current directory
mkcd [dir]
  Make directory (with parents) and change into it
extract [archive]
  Extract zip/tar archives into current directory
serve [port]
  Start a simple HTTP server (default 8000)
stopserve
  Stop running server
mops install [pkg]
  Install Python package using pip
wifcode [--show]
  List saved Wi-Fi profiles (password hidden by default)
calc [expr]
  Evaluate math expressions

TERMINAL FEATURES
──────────────────
newwindow
  Open a new terminal window
splitview
  Toggle split view (dual pane)
favorite [command]
  Add command to favorites
favorites
  List all favorite commands

TERMINAL CONTROL
─────────────────
help / ?
  Show help
exit
  Close terminal
"""
        self.append_text(help_text, color="green")

    # ---------------- Completer ----------------
    def update_completer_model(self):
        items = list(self.base_commands)
        items.extend(self.command_history[-50:])
        try:
            items.extend(os.listdir(self.current_dir))
        except Exception:
            pass
        seen = set()
        out = []
        for it in items:
            if it not in seen:
                seen.add(it)
                out.append(it)
        self.completer_model.setStringList(out)

    def list_dir(self):
        try:
            entries = os.listdir(self.current_dir)
            for name in sorted(entries):
                path = os.path.join(self.current_dir, name)
                if os.path.isdir(path):
                    self.append_text(f"{name}/\n", color="cyan")
                else:
                    self.append_text(f"{name}\n", color="white")
        except Exception as e:
            self.append_text(f"List error: {e}\n", color="red")

    def calc_expr(self, expr):
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            self.append_text(f"{result}\n", color="green")
        except Exception as e:
            self.append_text(f"Calc error: {e}\n", color="red")

    def print_tree(self, root, prefix="", max_depth=4, _depth=0):
        try:
            if _depth > max_depth:
                return
            entries = sorted(os.listdir(root))
            for i, name in enumerate(entries):
                path = os.path.join(root, name)
                connector = "└── " if i == len(entries)-1 else "├── "
                if os.path.isdir(path):
                    self.append_text(f"{prefix}{connector}{name}/\n", color="cyan")
                    self.print_tree(path, prefix + ("    " if i == len(entries)-1 else "│   "), max_depth, _depth+1)
                else:
                    self.append_text(f"{prefix}{connector}{name}\n", color="white")
        except Exception as e:
            self.append_text(f"Tree error: {e}\n", color="red")

    def show_wifi_passwords(self, show=False):
        if os.name != "nt":
            self.append_text("wifcode is only supported on Windows.\n", color="red", animate=False)
            return
        try:
            cmd = "netsh wlan show profiles"
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            out, err = proc.communicate()
            if err:
                self.append_text(f"Error fetching Wi-Fi profiles: {err}\n", color="red", animate=False)
                return
            profiles = []
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("All User Profile") or line.startswith("User Profile"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        name = parts[1].strip()
                        if name:
                            profiles.append(name)
            if not profiles:
                self.append_text("No saved Wi-Fi profiles found.\n", color="yellow", animate=False)
                return
            for profile in profiles:
                prof_cmd = f"netsh wlan show profile name=\"{profile}\" key=clear"
                p = subprocess.Popen(prof_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
                pout, perr = p.communicate()
                if perr:
                    self.append_text(f"{profile}: Error reading profile ({perr.strip()})\n", color="red", animate=False)
                    continue
                password = None
                for pline in pout.splitlines():
                    pl = pline.strip()
                    if pl.lower().startswith("key content"):
                        parts = pl.split(":", 1)
                        if len(parts) == 2:
                            password = parts[1].strip()
                            break
                if password:
                    if show:
                        self.append_text(f"{profile}: {password}\n", color="green", animate=False)
                    else:
                        self.append_text(f"{profile}: <hidden> (use 'wifcode --show')\n", color="yellow", animate=False)
                else:
                    self.append_text(f"{profile}: <no password or open network>\n", color="yellow", animate=False)
        except Exception as e:
            self.append_text(f"wifcode failed: {e}\n", color="red", animate=False)

    def search_files(self, pattern):
        try:
            count = 0
            for root, dirs, files in os.walk(self.current_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', errors='ignore') as fh:
                            for i, line in enumerate(fh, 1):
                                if pattern.lower() in line.lower():
                                    rel = os.path.relpath(fpath, self.current_dir)
                                    self.append_text(f"{rel}:{i}: {line.strip()}\n", color="white")
                                    count += 1
                    except Exception:
                        continue
            if count == 0:
                self.append_text("No matches found.\n", color="gray")
        except Exception as e:
            self.append_text(f"Search error: {e}\n", color="red")

    def make_and_cd(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            self.change_directory(path)
        except Exception as e:
            self.append_text(f"mkcd error: {e}\n", color="red")

    def extract_archive(self, path):
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
            if not os.path.exists(path):
                self.append_text("File is not real.\n", color="red")
                return
            if path.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(path, 'r') as z:
                    z.extractall(self.current_dir)
                self.append_text("Extracted zip archive.\n", color="green")
            elif any(path.endswith(ext) for ext in ('.tar', '.tar.gz', '.tgz', '.tar.bz2')):
                import tarfile
                with tarfile.open(path, 'r:*') as t:
                    t.extractall(self.current_dir)
                self.append_text("Extracted tar archive.\n", color="green")
            else:
                self.append_text("Unsupported archive type.\n", color="yellow")
        except Exception as e:
            self.append_text(f"Extract error: {e}\n", color="red")

    def start_server(self, port=8000):
        if self.server_process and self.server_process.poll() is None:
            self.append_text(f"Server already running (pid {self.server_process.pid}).\n", color="yellow")
            return
        try:
            cmd = [sys.executable, "-m", "http.server", str(port)]
            self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.current_dir)
            self.append_text(f"Serving {self.current_dir} at http://localhost:{port}/ (pid {self.server_process.pid})\n", color="green")
        except Exception as e:
            self.append_text(f"Serve error: {e}\n", color="red")

    def stop_server(self):
        if not self.server_process:
            self.append_text("No server running.\n", color="gray")
            return
        try:
            if self.server_process.poll() is None:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            self.append_text("Server stopped.\n", color="green")
        except Exception as e:
            self.append_text(f"Stop server error: {e}\n", color="red")
        finally:
            self.server_process = None

    def mops_install(self, package):
        try:
            self.append_text(f"Installing {package}...\n", color="cyan")
            cmd = [sys.executable, "-m", "pip", "install", package]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.append_text(line, color="white")
            proc.wait()
            if proc.returncode == 0:
                self.append_text(f"Installed {package}.\n", color="green")
            else:
                self.append_text(f"Installation failed (exit {proc.returncode}).\n", color="red")
        except Exception as e:
            self.append_text(f"mops install error: {e}\n", color="red")
    
    # ──────────────────  Multi-Window & Features ──────────────────
    def open_new_window(self):
        """Open a new independent terminal window."""
        try:
            new_window = MopsTerminal()
            new_window.show()
            self.append_text("✓ New terminal window opened.\n", color="green")
        except Exception as e:
            self.append_text(f"Error opening new window: {e}\n", color="red")
    
    def toggle_split_view(self):
        """Toggle split view mode with dual panes."""
        if self.split_view_enabled:
            # Disable split view
            self.layout.removeWidget(self.secondary_output)
            self.secondary_output.deleteLater()
            self.secondary_output = None
            self.split_view_enabled = False
            self.append_text("✓ Split view disabled.\n", color="yellow")
        else:
            # Enable split view
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self.output)
            
            self.secondary_output = QTextEdit()
            self.secondary_output.setReadOnly(True)
            monospace_font = QFont()
            monospace_font.setFamily("Consolas")
            monospace_font.setPointSize(10)
            self.secondary_output.setFont(monospace_font)
            self.secondary_output.setStyleSheet("""
                QTextEdit { background-color: #0d1117; color: #c9d1d9; border: none; margin: 0px; }
            """)
            
            splitter.addWidget(self.secondary_output)
            splitter.setSizes([500, 500])
            self.layout.insertWidget(0, splitter)
            self.layout.removeWidget(self.output)
            
            self.split_view_enabled = True
            self.secondary_output.insertPlainText("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            self.secondary_output.insertPlainText("Secondary pane ready for reference\n")
            self.secondary_output.insertPlainText("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            self.append_text("✓ Split view enabled! Use secondary pane for reference.\n", color="green")
    
    def load_favorites(self):
        """Load favorite commands from file."""
        fav_file = os.path.expanduser("~/.mops_favorites.json")
        try:
            if os.path.exists(fav_file):
                with open(fav_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_favorites(self):
        """Save favorite commands to file."""
        fav_file = os.path.expanduser("~/.mops_favorites.json")
        try:
            with open(fav_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            self.append_text(f"Error saving favorites: {e}\n", color="red")
    
    def add_favorite(self, command):
        """Add a command to favorites."""
        if command.strip():
            key = command.split()[0] if command else "fav"
            self.favorites[key] = command
            self.save_favorites()
            self.append_text(f"✓ Added to favorites: {command}\n", color="green")
        else:
            self.append_text("Please provide a command.\n", color="red")
    
    def list_favorites(self):
        """List all favorite commands."""
        if not self.favorites:
            self.append_text("No favorites yet. Use 'favorite [command]' to add one.\n", color="yellow")
            return
        
        self.append_text("\n━━━━━━━━━━ Favorite Commands ━━━━━━━━━━\n", color="cyan")
        for key, cmd in self.favorites.items():
            self.append_text(f"  {key:20} → {cmd}\n", color="white")
        self.append_text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", color="cyan")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = MopsTerminal()
    terminal.show()
    sys.exit(app.exec_())
