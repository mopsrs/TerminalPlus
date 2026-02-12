# -*- coding: utf-8 -*-
import sys
import subprocess
import os
import json
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QCompleter, QSplitter, QPushButton, QLabel, QDialog, QMenu, QAction, QStyle, QSizePolicy, QFrame, QGraphicsDropShadowEffect, QScrollBar
from PyQt5.QtGui import QFont, QColor, QTextCursor, QTextCharFormat, QPainter, QBrush, QPen, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, QStringListModel, QObject, QEvent, QPropertyAnimation, QRect, pyqtSignal, pyqtProperty, QEasingCurve


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


class LeverToggle(QWidget):
    """A modern iOS/macOS-style sliding toggle with smooth animation."""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked=False, width=52, height=30):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._on = checked
        self._offset = 1.0 if self._on else 0.0
        self._anim = QPropertyAnimation(self, b"offset")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.width(), self.height())

    def mouseReleaseEvent(self, event):
        self.setChecked(not self._on)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        radius = h / 2

        # track
        track_rect = QRect(0, 0, w, h)
        grad = QBrush(QColor(220, 220, 220))
        if self._on:
            grad = QBrush(QColor(100, 200, 120))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(track_rect, radius, radius)

        # shadow under knob
        knob_d = h - 6
        knob_x = int(3 + (w - knob_d - 6) * self._offset)
        knob_rect = QRect(knob_x, 3, knob_d, knob_d)
        shadow = QBrush(QColor(0, 0, 0, 30))
        p.setBrush(shadow)
        p.drawEllipse(knob_rect.adjusted(0, 2, 0, 2))

        # knob
        knob_brush = QBrush(QColor(255, 255, 255))
        p.setBrush(knob_brush)
        p.setPen(QPen(QColor(200, 200, 200, 120)))
        p.drawEllipse(knob_rect)

    def isChecked(self):
        return self._on

    def setChecked(self, val: bool):
        if self._on == val:
            return
        self._on = val
        start = self._offset
        end = 1.0 if val else 0.0
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
        self.toggled.emit(self._on)

    def getOffset(self):
        return self._offset

    def setOffset(self, v):
        self._offset = float(v)
        self.update()

    offset = pyqtProperty(float, fget=getOffset, fset=setOffset)


class MopsTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.current_dir = os.getcwd()

        # Window setup
        self.setWindowTitle("mopsrs terminal")
        self.setGeometry(100, 100, 1400, 800)
        
        # Enhanced Ghostty-style theme with subtle panels and ghostly scrollbars
        self.setStyleSheet("""
            QWidget { background-color: #0f0f0f; color: #d0d0d0; }
            QTextEdit { background-color: #0f0f0f; color: #d0d0d0; border: none; margin: 0px; padding: 8px; }
            QLineEdit { background-color: #0f0f0f; color: #d0d0d0; border: none; padding: 4px; margin: 0px; }
            QLineEdit:focus { border: none; }
            QFrame { background-color: #0f0f0f; border: none; }
            
            /* Ghostly scrollbar styling */
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 3px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            /* Apple-style toggle switches */
            LeverToggle {
                background: transparent;
                border: none;
            }
            
            /* Settings panel styling */
            QLabel { color: #d0d0d0; }
        """)

        # Main horizontal layout with splitter for terminal and settings
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #1a1a1a; width: 2px; } QSplitter { background-color: #0f0f0f; }")
        
        # ============ Terminal Container (Left/Center) ============
        self.terminal_container = QFrame()
        self.terminal_container.setStyleSheet("""
            QFrame { 
                background-color: #0f0f0f; 
                border: 1px solid #1a1a1a;
                border-radius: 4px;
            }
        """)
        terminal_layout = QVBoxLayout()
        terminal_layout.setSpacing(0)
        terminal_layout.setContentsMargins(15, 15, 15, 15)
        self.terminal_container.setLayout(terminal_layout)

        # Terminal output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        monospace_font = QFont()
        # Use a cleaner monospace font
        for font_name in ["Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas"]:
            monospace_font.setFamily(font_name)
            test_font = QFont(font_name)
            if test_font.exactMatch():
                break
        monospace_font.setPointSize(11)
        self.output.setFont(monospace_font)
        self.output.setStyleSheet("""
            QTextEdit { 
                background-color: #0a0a0a; 
                color: #d0d0d0; 
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 8px;
                margin: 0px;
            }
        """)
        # Style the scrollbar for the output widget
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setStyleSheet("""
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
        """)
        terminal_layout.addWidget(self.output, 1)

        # Input line
        self.input = QLineEdit()
        self.input.setFont(monospace_font)
        self.input.setPlaceholderText("$ ")
        self.input.setStyleSheet("""
            QLineEdit { 
                background-color: #0a0a0a; 
                color: #d0d0d0; 
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 6px 8px;
                margin: 8px 0px 0px 0px;
            }
            QLineEdit:focus { 
                border: 1px solid #2a4a6a;
                padding: 6px 8px;
            }
            QLineEdit::placeholder { color: #4a4a4a; }
        """)
        terminal_layout.addWidget(self.input)
        self.input.returnPressed.connect(self.handle_command)
        
        # Install custom key press handler using event filter
        self._input_filter = InputKeyFilter(self)
        self.input.installEventFilter(self._input_filter)

        # Split view area (initially hidden)
        self.split_container = QFrame()
        self.split_container.setVisible(False)
        self.split_container.setStyleSheet("""
            QFrame { 
                background-color: #0f0f0f; 
                border: 1px solid #1a1a1a;
                border-radius: 4px;
            }
        """)
        split_layout = QVBoxLayout()
        split_layout.setSpacing(0)
        split_layout.setContentsMargins(15, 15, 15, 15)
        self.split_container.setLayout(split_layout)

        # Secondary output for split view
        self.secondary_output = QTextEdit()
        self.secondary_output.setReadOnly(True)
        self.secondary_output.setFont(monospace_font)
        self.secondary_output.setStyleSheet("""
            QTextEdit { 
                background-color: #0a0a0a; 
                color: #d0d0d0; 
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 8px;
            }
        """)
        split_layout.addWidget(self.secondary_output)

        # Secondary input
        self.secondary_input = QLineEdit()
        self.secondary_input.setFont(monospace_font)
        self.secondary_input.setPlaceholderText("$ ")
        self.secondary_input.setStyleSheet("""
            QLineEdit { 
                background-color: #0a0a0a; 
                color: #d0d0d0; 
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 6px 8px;
                margin: 8px 0px 0px 0px;
            }
            QLineEdit:focus { 
                border: 1px solid #2a4a6a;
            }
        """)
        split_layout.addWidget(self.secondary_input)
        self.secondary_input.returnPressed.connect(self.handle_secondary_command)

        # Terminal splitter (for horizontal/vertical splits)
        self.terminal_splitter = QSplitter(Qt.Vertical)
        self.terminal_splitter.setStyleSheet("QSplitter::handle { background-color: #1a1a1a; height: 2px; }")
        self.terminal_splitter.addWidget(self.terminal_container)
        self.terminal_splitter.addWidget(self.split_container)
        self.terminal_splitter.setStretchFactor(0, 1)
        self.terminal_splitter.setStretchFactor(1, 1)

        # ============ Settings Panel (Right) ============
        self.settings_panel = QFrame()
        self.settings_panel.setMaximumWidth(260)
        self.settings_panel.setMinimumWidth(180)
        self.settings_panel.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border-left: none;
                border-radius: 0px;
            }
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(0)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        self.settings_panel.setLayout(settings_layout)

        # Settings title
        settings_title = QLabel("settings")
        settings_title.setStyleSheet("QLabel { color: #5a5a5a; font-weight: normal; font-size: 12px; letter-spacing: 1px; margin-bottom: 12px; }")
        settings_layout.addWidget(settings_title)

        # Display & Output section header
        display_label = QLabel("display")
        display_label.setStyleSheet("QLabel { color: #3a3a3a; font-size: 10px; letter-spacing: 0.5px; margin-top: 8px; margin-bottom: 6px; }")
        settings_layout.addWidget(display_label)

        # Line wrap toggle
        wrap_container = QHBoxLayout()
        wrap_container.setSpacing(8)
        wrap_container.setContentsMargins(0, 4, 0, 4)
        wrap_label = QLabel("line wrap")
        wrap_label.setStyleSheet("QLabel { color: #8a8a8a; font-size: 12px; }")
        self.toggle_wrap = LeverToggle(checked=False, width=44, height=22)
        self.toggle_wrap.toggled.connect(self.toggle_line_wrap)
        wrap_container.addWidget(wrap_label)
        wrap_container.addStretch()
        wrap_container.addWidget(self.toggle_wrap)
        settings_layout.addLayout(wrap_container)

        # Timestamps toggle
        ts_container = QHBoxLayout()
        ts_container.setSpacing(8)
        ts_container.setContentsMargins(0, 4, 0, 4)
        ts_label = QLabel("timestamps")
        ts_label.setStyleSheet("QLabel { color: #8a8a8a; font-size: 12px; }")
        self.toggle_timestamps = LeverToggle(checked=False, width=44, height=22)
        self.toggle_timestamps.toggled.connect(self.toggle_timestamps_display)
        ts_container.addWidget(ts_label)
        ts_container.addStretch()
        ts_container.addWidget(self.toggle_timestamps)
        settings_layout.addLayout(ts_container)
        # Ghostly timestamp
        ts_time = QLabel(time.strftime('%H:%M'))
        ts_time.setStyleSheet("QLabel { color: #3a3a3a; font-size: 8px; margin-left: 16px; margin-top: -2px; }")
        settings_layout.addWidget(ts_time)

        # Terminal & Control section
        terminal_section = QLabel("terminal")
        terminal_section.setStyleSheet("QLabel { color: #3a3a3a; font-size: 10px; letter-spacing: 0.5px; margin-top: 10px; margin-bottom: 6px; }")
        settings_layout.addWidget(terminal_section)

        # Advanced mode toggle
        adv_container = QHBoxLayout()
        adv_container.setSpacing(8)
        adv_container.setContentsMargins(0, 4, 0, 4)
        adv_label = QLabel("advanced")
        adv_label.setStyleSheet("QLabel { color: #8a8a8a; font-size: 12px; }")
        self.toggle_advanced = LeverToggle(checked=False, width=44, height=22)
        self.toggle_advanced.toggled.connect(self.toggle_advanced_mode_ui)
        adv_container.addWidget(adv_label)
        adv_container.addStretch()
        adv_container.addWidget(self.toggle_advanced)
        settings_layout.addLayout(adv_container)
        # Ghostly timestamp
        adv_time = QLabel(time.strftime('%H:%M'))
        adv_time.setStyleSheet("QLabel { color: #3a3a3a; font-size: 7px; margin-left: 16px; margin-top: -2px; }")
        settings_layout.addWidget(adv_time)

        # Split view button
        self.split_view_button = QPushButton("split view")
        self.split_view_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6a6a6a;
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 5px;
                font-size: 10px;
                margin: 8px 0px 0px 0px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                color: #8a8a8a;
                border: 1px solid #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #0a0a0a;
            }
        """)
        self.split_view_button.clicked.connect(self.toggle_split_view)
        settings_layout.addWidget(self.split_view_button)

        # Info section
        info_section = QLabel("info")
        info_section.setStyleSheet("QLabel { color: #3a3a3a; font-size: 10px; letter-spacing: 0.5px; margin-top: 10px; margin-bottom: 6px; }")
        settings_layout.addWidget(info_section)

        # Current directory display
        self.dir_label = QLabel("")
        self.dir_label.setStyleSheet("QLabel { color: #7a7a7a; font-size: 11px; word-wrap: true; line-height: 1.4; }")
        self.dir_label.setWordWrap(True)
        self.update_dir_label()
        settings_layout.addWidget(self.dir_label)
        # Ghostly timestamp for directory
        dir_time = QLabel(time.strftime('%H:%M:%S'))
        dir_time.setStyleSheet("QLabel { color: #2a2a2a; font-size: 8px; margin-top: 2px; }")
        settings_layout.addWidget(dir_time)

        # Stretch at bottom
        settings_layout.addStretch()

        # Add terminal and settings to main splitter
        self.main_splitter.addWidget(self.terminal_splitter)
        self.main_splitter.addWidget(self.settings_panel)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 0)
        self.main_splitter.setSizes([1000, 250])
        
        main_layout.addWidget(self.main_splitter)

        # ============ Floating Timestamp (Top Right) ============
        self.timestamp_widget = QLabel(time.strftime('%H:%M:%S'))
        self.timestamp_widget.setStyleSheet("""
            QLabel {
                color: #3a3a3a;
                font-size: 9px;
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 3px;
            }
        """)
        self.timestamp_widget.setAlignment(Qt.AlignRight | Qt.AlignTop)
        # Set position for floating timestamp
        timestamp_timer = QTimer(self)
        timestamp_timer.timeout.connect(self.update_timestamp)
        timestamp_timer.start(1000)  # Update every second

        # Completer
        self.base_commands = [
            "help", "?", "clear", "cls", "exit", "pwd", "cd", "ls", "dir",
            "whoami", "systeminfo", "ipconfig", "tasklist", "mkdir", "del", "copy",
            "type", "calc", "tree", "open", "echo",
            "search", "mkcd", "extract", "serve", "stopserve", "mops", "mops install", "wifcode",
            "newwindow", "splitview", "favorite", "favorites", "advancedmode", "tutorial"
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
        
        # Split view tracking
        self.split_view_enabled = False
        self.split_orientation = "vertical"  # or "horizontal"
        
        # Tutorial and advanced mode
        self.tutorial_mode = False
        self.advanced_mode = False
        # timestamp setting
        self.show_timestamps = False
        # line wrap setting
        self.line_wrap_enabled = False
        
        # Show startup screen for user selection
        self.show_startup_screen()

    # ---------------- UI / Animation ----------------
    def append_text(self, text, color="default", animate=True):
        """Append text to output with specified color and optional animation."""
        # Ghostty-style color palette
        color_map = {
            "cyan": "#8be9fd",
            "green": "#50fa7b",
            "red": "#ff5555",
            "yellow": "#f1fa8c",
            "white": "#f8f8f2",
            "default": "#d0d0d0",
            "gray": "#6272a4",
            "black": "#0f0f0f",
        }
        html_color = color_map.get(color, color_map["default"])
        
        # Add timestamp prefix if enabled
        try:
            prefix = f"[{time.strftime('%H:%M:%S')}] " if getattr(self, 'show_timestamps', False) else ""
        except Exception:
            prefix = ""
        full_text = prefix + text

        # If not animating, just insert directly
        if not animate:
            cursor = self.output.textCursor()
            cursor.movePosition(QTextCursor.End)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(html_color))
            cursor.setCharFormat(fmt)
            cursor.insertText(full_text)
            self.output.setTextCursor(cursor)
            self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())
            # also send to panels
            try:
                self._broadcast_to_panels(full_text)
            except Exception:
                pass
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
                # once animation has finished, broadcast full text to panels
                try:
                    self._broadcast_to_panels(full_text)
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

    def _broadcast_to_panels(self, text):
        """Send a copy of the text to any attached panels depending on their type."""
        try:
            # skip status/setup messages to avoid duplication
            low_text = text.lower()
            if any(x in low_text for x in ('advanced mode', 'timestamps', 'line wrap', 'panels', 'safe mode')):
                return
            
            for entry in list(getattr(self, 'panels', []) or []):
                try:
                    ptype = entry.get('type', 'output').lower()
                    pane = entry.get('pane')
                    if not pane:
                        continue
                    send = False
                    if ptype in ('output', 'aux', 'terminal'):
                        send = True
                    elif ptype == 'log':
                        send = True
                    elif ptype == 'debug':
                        if any(k in low_text for k in ('error', 'failed', 'exception', 'traceback', 'warning')):
                            send = True
                    if send:
                        pane.moveCursor(QTextCursor.End)
                        pane.insertPlainText(text)
                        pane.verticalScrollBar().setValue(pane.verticalScrollBar().maximum())
                except Exception:
                    continue
        except Exception:
            pass

    def _type_logo(self, logo_text):
        """Display logo text with animation."""
        self.output.clear()
        self.append_text(logo_text, color="white", animate=True)

    # ----------------  Startup Screen ----------------
    def show_startup_screen(self):
        """Display the initial startup screen with user options."""
        splash = "mopsrs terminal\nType 'help' for commands.\n\n"
        self.output.clear()
        self.append_text(splash, color="cyan", animate=False)
        self.input.setFocus()
        # show a small dialog with the two quick choices
        QTimer.singleShot(150, self.show_startup_dialog)

    def show_startup_dialog(self):
        """Present a simple dialog with two options for new/experienced users."""
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Getting Started")
            layout = QHBoxLayout()
            dlg.setLayout(layout)

            btn_new = QPushButton("I don't know what I'm doing")
            btn_new.clicked.connect(lambda: (dlg.accept(), self.show_tutorial()))
            layout.addWidget(btn_new)

            btn_exp = QPushButton("I know what I'm doing")
            btn_exp.clicked.connect(lambda: (dlg.accept(), self.show_welcome()))
            layout.addWidget(btn_exp)

            dlg.setModal(True)
            dlg.exec_()
        except Exception:
            # fallback: nothing
            pass

    def show_tutorial(self):
        """Display comprehensive tutorial for new users."""
        self.tutorial_mode = True
        tutorial = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    MOPS TERMINAL - BEGINNER'S GUIDE                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📚 BASIC COMMANDS
─────────────────────────────────────────────────────────────────────────────────

Navigation:
  • pwd              See where you are right now
  • cd folder_name   Move to a different folder
  • ls or dir        List all files and folders
  • cd ..            Go back to parent folder

System Info:
  • whoami           Show your username
  • systeminfo       Display computer information
  • tasklist         See running programs

File Operations:
  • copy src dst     Copy a file
  • del filename     Delete a file
  • mkdir foldername Create a new folder
  • type filename    View file contents

🎯 ESSENTIAL TRICKS
─────────────────────────────────────────────────────────────────────────────────

Split View - See two things at once:
  1. Type: splitview
  2. Press Enter
  3. You'll see two panels side by side!
  4. Main panel = your commands, Right panel = notes/reference

Command History:
  • Press UP/DOWN arrows to go through previous commands
  • Don't retype the same thing twice!

Autocomplete:
  • Type part of a command
  • Press TAB to auto-complete
  • Super useful for long folder names!

Favorites - Save your most used commands:
  • Type: favorite ls /s /b
  • View them: favorites
  • Quickly see all your saved shortcuts!

Multiple Windows:
  • Type: newwindow
  • Opens a brand new terminal window
  • Run 2 tasks at once!

🔧 QUICK EXAMPLES
─────────────────────────────────────────────────────────────────────────────────

Example 1 - Explore files:
  > cd Desktop
  > ls
  > tree

Example 2 - Create something:
  > mkcd MyProject
  > mkdir src
  > mkdir assets

Example 3 - Quick math:
  > calc 42 * 2
  Result: 84

Example 4 - Start a web server:
  > serve 8000
  > (Visit http://localhost:8000 in your browser!)

Example 5 - Install tools:
  > mops install requests
  > (Installs Python packages!)

⚡ UPGRADE TO ADVANCED MODE
─────────────────────────────────────────────────────────────────────────────────

Ready to unlock power user features?

  Type: advancedmode on

Advanced mode enables:
  ✓ PowerShell commands ($variables, pipes |)
  ✓ Complex scripts and piping
  ✓ System optimization tools
  ✓ Power user shortcuts
  ✓ Advanced file operations
  ✓ Direct system command access

💡 PRO TIPS
─────────────────────────────────────────────────────────────────────────────────

  1. Use 'help' anytime to see all commands
  2. Customize favorites for YOUR workflow
  3. Split screen is amazing for comparing files
  4. Check 'ipconfig' to see your network
  5. 'tree /L:2' shows folder structure 2 levels deep
  6. You can run ANY Windows command here!

🎓 NEXT STEPS
─────────────────────────────────────────────────────────────────────────────────

  1. Try navigating your computer with 'cd' and 'ls'
  2. Enable split view with 'splitview'
  3. Add a favorite command with 'favorite [command]'
  4. When comfortable, type 'advancedmode on'
  5. Read full help with 'help' anytime

═══════════════════════════════════════════════════════════════════════════════

Ready? Start typing commands!  Type 'exit' to quit anytime.

═══════════════════════════════════════════════════════════════════════════════
"""
        self.output.clear()
        self.append_text(tutorial, color="green", animate=False)
        self.append_text("\n> ", color="yellow", animate=False)

    def show_welcome(self):
        """Show minimal welcome message."""
        self.output.clear()
        logo = "mopsrs terminal\n"
        self.append_text(logo, color="cyan", animate=False)
        self.append_text("\n", color="default", animate=False)

    # ---------------- Input handling ----------------
    def handle_command(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.append_text(f"\n> {cmd}\n", color="yellow")
        self.input.clear()

        # Handle startup screen selection
        low = cmd.lower()
        
        # First-time user selection
        if low in ("1", "help") and not self.tutorial_mode:
            self.show_tutorial()
            return
        elif low in ("2", "start") and not self.tutorial_mode:
            self.show_welcome()
            return

        # Builtin commands
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
        elif low == "tutorial":
            self.show_tutorial()
        elif low.startswith("advancedmode"):
            self.toggle_advanced_mode(cmd)
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
            self.update_dir_label()
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
                        self.append_text(line + "\n", color="red", animate=False)
                    elif "warning" in low:
                        self.append_text(line + "\n", color="yellow", animate=False)
                    else:
                        self.append_text(line + "\n", color="white", animate=False)
            if stderr:
                self.append_text(stderr, color="red", animate=False)
            if not stdout and not stderr:
                self.append_text("[Command executed]\n", color="gray", animate=False)
        except Exception as e:
            self.append_text(f"Execution error: {e}\n", color="red", animate=False)

    # ---------------- Help ----------------
    def show_help(self, animated=False):
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
  Toggle split view (dual pane with draggable resize)
favorite [command]
  Add command to favorites
favorites
  List all favorite commands

POWER USER MODE
────────────────
advancedmode on
  Unlock advanced features (PowerShell, pipes, scripts)
advancedmode off
  Disable advanced mode
advancedmode
  Check status of advanced mode

HELP & LEARNING
────────────────
help / ?
  Show this help menu
tutorial
  Show the beginner's tutorial

TERMINAL CONTROL
─────────────────
exit
  Close terminal
"""
        # animate help display for clarity
        if animated:
            try:
                self.append_text(help_text, color="white", animate=True)
                return
            except Exception:
                pass
        self.append_text(help_text, color="white", animate=False)

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
        """Toggle split view for dual-pane terminal."""
        self.split_view_enabled = not self.split_view_enabled
        self.split_container.setVisible(self.split_view_enabled)
        
        if self.split_view_enabled:
            self.append_text("✓ Split view enabled. Type commands in either pane.\n", color="green")
            self.secondary_output.clear()
            self.secondary_output.setPlainText("Secondary pane ready for input.\n")
        else:
            self.append_text("✓ Split view disabled.\n", color="green")
            self.split_container.setVisible(False)

    def handle_secondary_command(self):
        """Handle commands from the secondary (split view) pane."""
        cmd = self.secondary_input.text().strip()
        if not cmd:
            return
        self.secondary_output.append(f"\n$ {cmd}")
        self.secondary_input.clear()

        # Handle command in secondary pane
        low = cmd.lower()
        
        if low in ("help", "?"):
            self.secondary_output.append("\nAvailable commands: pwd, cd, ls, dir, tree, calc, whoami\n")
        elif low in ("clear", "cls"):
            self.secondary_output.clear()
        elif low.startswith("cd "):
            self.secondary_output.append(f"cd not available in secondary pane\n")
        elif low in ("pwd", "cd"):
            self.secondary_output.append(f"{self.current_dir}\n")
        elif low in ("ls", "dir"):
            try:
                entries = os.listdir(self.current_dir)
                for name in sorted(entries):
                    self.secondary_output.append(name)
            except Exception as e:
                self.secondary_output.append(f"Error: {e}")
        else:
            # Try to execute in secondary pane
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, cwd=self.current_dir)
                stdout, stderr = process.communicate()
                if stdout:
                    self.secondary_output.append(stdout)
                if stderr:
                    self.secondary_output.append(f"[Error] {stderr}")
            except Exception as e:
                self.secondary_output.append(f"Error: {e}\n")

    def add_panel(self, panel_type="output"):
        """Panels are now integrated as split view."""
        pass

    def update_dir_label(self):
        """Update the directory label in the settings panel."""
        try:
            short_dir = os.path.basename(self.current_dir) or self.current_dir
            if not short_dir:
                short_dir = self.current_dir
            self.dir_label.setText(short_dir)
        except Exception:
            self.dir_label.setText("directory")

    def toggle_line_wrap(self, enabled):
        """Toggle line wrap in the output."""
        self.line_wrap_enabled = enabled
        if enabled:
            self.output.setLineWrapMode(QTextEdit.WidgetWidth)
            if hasattr(self, 'secondary_output'):
                self.secondary_output.setLineWrapMode(QTextEdit.WidgetWidth)
            self.append_text("✓ Line wrap enabled.\n", color="green")
        else:
            self.output.setLineWrapMode(QTextEdit.NoWrap)
            if hasattr(self, 'secondary_output'):
                self.secondary_output.setLineWrapMode(QTextEdit.NoWrap)
            self.append_text("✓ Line wrap disabled.\n", color="green")

    def update_timestamp(self):
        """Update the floating timestamp."""
        try:
            if hasattr(self, 'timestamp_widget'):
                self.timestamp_widget.setText(time.strftime('%H:%M:%S'))
        except Exception:
            pass

    def toggle_timestamps_display(self, enabled):
        """Toggle timestamp display in output."""
        self.show_timestamps = enabled
        if enabled:
            self.append_text("✓ Timestamps enabled.\n", color="green")
        else:
            self.append_text("✓ Timestamps disabled.\n", color="green")

    def toggle_advanced_mode_ui(self, enabled):
        """Toggle advanced mode from UI toggle."""
        if enabled:
            self.toggle_advanced_mode("advancedmode on")
        else:
            self.toggle_advanced_mode("advancedmode off")
    
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
    
    def toggle_advanced_mode(self, cmd):
        """Toggle advanced mode with powerful features."""
        parts = cmd.lower().split()
        
        if len(parts) < 2:
            if self.advanced_mode:
                self.append_text("Advanced mode is ON. Type 'advancedmode off' to disable.\n", color="cyan")
            else:
                self.append_text("Advanced mode is OFF. Type 'advancedmode on' to enable.\n", color="yellow")
            return
        
        action = parts[1]
        
        if action == "on":
            if self.advanced_mode:
                self.append_text("Advanced mode already enabled!\n", color="yellow")
                return
            
            self.advanced_mode = True
            self.tutorial_mode = False  # Exit tutorial mode
            # Sync UI toggle with state
            try:
                self.toggle_advanced.blockSignals(True)
                self.toggle_advanced.setChecked(True)
                self.toggle_advanced.blockSignals(False)
            except Exception:
                pass
            
            advanced_screen = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                   🔥 ADVANCED MODE ACTIVATED 🔥                             ║
║                                                                               ║
║                    POWER USER FEATURES UNLOCKED                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

⚡ ADVANCED FEATURES ENABLED:

  1. PIPES & STREAMS
     > dir | grep .txt        (Filter command output)
     > tasklist | find "python"  (Find specific processes)
     > Get-Process | Sort-Object CPU -Descending  (PowerShell pipes)

  2. VARIABLES & EXPRESSIONS
     > set MY_VAR=hello && echo %MY_VAR%  (CMD variables)
     > $files = Get-ChildItem | wc      (PowerShell variables)

  3. ADVANCED POWERSHELL
     > Get-ExecutionPolicy
     > Set-Alias
     > Where-Object, Select-Object filters
     > Invoke-WebRequest (download files)
     > ConvertTo-Json, ConvertFrom-Json

  4. BATCH SCRIPTING
     > Create .bat files with goto, for loops, functions
     > Use delayed expansion !VAR!
     > Conditional operations (if-else)

  5. COMMAND CHAINING
     > command1 && command2      (Run second if first succeeds)
     > command1 || command2      (Run second if first fails)
     > (command1) | (command2)   (Pipe output)

  6. NETWORK TOOLS
     > ping -t 8.8.8.8           (Continuous ping)
     > nslookup example.com      (DNS lookup)
     > tracert google.com        (Trace route)

  7. PERFORMANCE & MONITORING
     > Get-Process | Sort-Object WorkingSet -Descending
     > wmic OS get Name,BuildNumber
     > systeminfo | findstr Build
     > CPU usage monitoring

═══════════════════════════════════════════════════════════════════════════════

🎯 PRO TIPS:

  1. Use 'get-help cmdlet' for PowerShell command help
  2. Combine commands with | for powerful workflows
  3. Create .bat files for complex multi-command operations
  4. Use 'splitview' to divide terminal into resizable panes
  5. Run 'calc' for complex math operations
  6. Check 'help' anytime to see all available commands
  7. Drag the middle separator to resize terminal panes

═══════════════════════════════════════════════════════════════════════════════

Advanced mode enabled! You now have full system access.
Type 'advancedmode off' to return to normal mode.
Type 'help' to see all commands.

═══════════════════════════════════════════════════════════════════════════════
"""
            # do not clear existing terminal output; append advanced notice
            self.append_text("\n" + advanced_screen, color="cyan", animate=False)
            
        elif action == "off":
            if not self.advanced_mode:
                self.append_text("Advanced mode already disabled!\n", color="yellow")
                return
            
            self.advanced_mode = False
            # Sync UI toggle with state
            try:
                self.toggle_advanced.blockSignals(True)
                self.toggle_advanced.setChecked(False)
                self.toggle_advanced.blockSignals(False)
            except Exception:
                pass
            self.append_text("✓ Advanced mode disabled. Back to safe mode!\n", color="green")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = MopsTerminal()
    terminal.show()
    sys.exit(app.exec_())
