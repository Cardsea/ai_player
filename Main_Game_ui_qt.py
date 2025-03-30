import sys
import os
import time
import requests
import threading
from queue import Queue
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QComboBox, 
                           QTextEdit, QDialog, QScrollArea, QFrame, 
                           QSlider, QGroupBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Game Settings
        game_group = QGroupBox("Game Settings")
        game_layout = QVBoxLayout()
        
        # AI Thinking Time
        wait_layout = QHBoxLayout()
        wait_label = QLabel("AI Thinking Time (seconds):")
        self.wait_time = QDoubleSpinBox()
        self.wait_time.setRange(0.5, 5.0)
        self.wait_time.setSingleStep(0.1)
        self.wait_time.setValue(1.0)
        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.wait_time)
        game_layout.addLayout(wait_layout)
        
        # History Size
        history_layout = QHBoxLayout()
        history_label = QLabel("Game History Size:")
        self.history_size = QSpinBox()
        self.history_size.setRange(5, 20)
        self.history_size.setValue(10)
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_size)
        game_layout.addLayout(history_layout)
        
        game_group.setLayout(game_layout)
        layout.addWidget(game_group)
        
        # Display Settings
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        
        # Font Size
        font_layout = QHBoxLayout()
        font_label = QLabel("Text Size:")
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 20)
        self.font_size.setValue(14)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_size)
        display_layout.addLayout(font_layout)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # AI Settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QVBoxLayout()
        
        # Model Selection
        model_layout = QHBoxLayout()
        model_label = QLabel("AI Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(['llama3', 'mistral', 'codellama'])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        ai_layout.addLayout(model_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel("AI Creativity:")
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.1, 1.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature)
        ai_layout.addLayout(temp_layout)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Adventure AI Player")
        self.setMinimumSize(1200, 800)
        
        # Initialize settings
        self.current_wait_time = 1.0
        self.max_history_size = 10
        self.font_size = 14
        self.ai_model = 'llama3'
        self.ai_temperature = 0.7
        
        # Set up colors
        self.window_bg = QColor('#1A1A1A')  # Soft black
        self.text_bg = QColor('#2A2A2A')    # Slightly lighter than window
        self.text_fg = QColor('#E0E0E0')    # Soft white
        self.thinking_color = QColor('#D4B483')  # Dark yellow
        self.ai_response_color = QColor('#9B6B9E')  # Dark purple
        self.game_output_color = QColor('#7A9B7A')  # Dark green
        self.button_bg = QColor('#2A2A2A')  # Same as text background
        self.button_hover = QColor('#3A3A3A')  # Even lighter for hover
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create title
        title = QLabel("Text Adventure AI Player")
        title.setFont(QFont('Helvetica', 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create game selector
        selector_layout = QHBoxLayout()
        game_label = QLabel("Select Game:")
        game_label.setFont(QFont('Helvetica', 14))
        selector_layout.addWidget(game_label)
        
        self.game_combo = QComboBox()
        self.game_combo.setFont(QFont('Helvetica', 12))
        self.games = [f for f in os.listdir('games') if f.endswith('.z5')]
        self.games.sort()
        self.game_combo.addItems(self.games)
        self.game_combo.setCurrentText("zork1.z5")
        selector_layout.addWidget(self.game_combo)
        layout.addLayout(selector_layout)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_game)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_game)
        self.reset_button.setEnabled(False)
        
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.quit_game)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.quit_button)
        layout.addLayout(button_layout)
        
        # Create text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont('Helvetica', self.font_size))
        self.text_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.text_bg.name()};
                color: {self.text_fg.name()};
                border: 1px solid {self.text_fg.name()}40;
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.text_display)
        
        # Initialize game variables
        self.text_player = None
        self.game_thread = None
        self.is_running = False
        self.output_queue = Queue()
        self.game_process = None
        
        # Set up output queue timer
        self.output_timer = QTimer()
        self.output_timer.timeout.connect(self.check_output_queue)
        self.output_timer.start(100)
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def apply_dark_theme(self):
        """Apply dark theme to the entire application"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, self.window_bg)
        palette.setColor(QPalette.ColorRole.WindowText, self.text_fg)
        palette.setColor(QPalette.ColorRole.Base, self.text_bg)
        palette.setColor(QPalette.ColorRole.AlternateBase, self.window_bg)
        palette.setColor(QPalette.ColorRole.ToolTipBase, self.window_bg)
        palette.setColor(QPalette.ColorRole.ToolTipText, self.text_fg)
        palette.setColor(QPalette.ColorRole.Text, self.text_fg)
        palette.setColor(QPalette.ColorRole.Button, self.button_bg)
        palette.setColor(QPalette.ColorRole.ButtonText, self.text_fg)
        palette.setColor(QPalette.ColorRole.BrightText, self.text_fg)
        palette.setColor(QPalette.ColorRole.Link, self.ai_response_color)
        palette.setColor(QPalette.ColorRole.Highlight, self.ai_response_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, self.text_fg)
        
        QApplication.setPalette(palette)
        
        # Set stylesheet for widgets that need additional styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.window_bg.name()};
            }}
            QPushButton {{
                background-color: {self.button_bg.name()};
                color: {self.text_fg.name()};
                border: 1px solid {self.text_fg.name()}40;
                padding: 5px;
                min-width: 100px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {self.button_hover.name()};
            }}
            QPushButton:disabled {{
                color: {self.text_fg.name()}80;
                border-color: {self.text_fg.name()}80;
            }}
            QComboBox {{
                background-color: {self.button_bg.name()};
                color: {self.text_fg.name()};
                border: 1px solid {self.text_fg.name()}40;
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QGroupBox {{
                background-color: {self.button_bg.name()};
                color: {self.text_fg.name()};
                border: 1px solid {self.text_fg.name()}40;
                margin-top: 1em;
                padding-top: 10px;
                border-radius: 5px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            QLabel {{
                color: {self.text_fg.name()};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.button_bg.name()};
                color: {self.text_fg.name()};
                border: 1px solid {self.text_fg.name()}40;
                padding: 5px;
                border-radius: 3px;
            }}
        """)
    
    def check_output_queue(self):
        """Check for new output in the queue and update the display"""
        try:
            while True:
                text = self.output_queue.get_nowait()
                if "AI Reasoning:" in text:
                    self.text_display.append(f'<span style="color: {self.thinking_color.name()}">{text}</span><br>')
                elif text.startswith(">"):
                    self.text_display.append(f'<span style="color: {self.ai_response_color.name()}">{text}</span><br>')
                else:
                    self.text_display.append(f'<span style="color: {self.game_output_color.name()}">{text}</span><br>')
                self.text_display.verticalScrollBar().setValue(
                    self.text_display.verticalScrollBar().maximum()
                )
        except:
            pass
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_wait_time = dialog.wait_time.value()
            self.max_history_size = dialog.history_size.value()
            self.font_size = dialog.font_size.value()
            self.ai_model = dialog.model_combo.currentText()
            self.ai_temperature = dialog.temperature.value()
            
            # Apply font size
            self.text_display.setFont(QFont('Helvetica', self.font_size))
    
    def start_game(self):
        """Start a new game"""
        if self.is_running:
            return
            
        # Check if Ollama is running and start it if needed
        try:
            response = requests.get("http://localhost:11434/api/version")
            if response.status_code != 200:
                self.start_ollama_server()
        except requests.exceptions.ConnectionError:
            self.start_ollama_server()
            
        self.is_running = True
        self.start_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        
        # Clear the display
        self.text_display.clear()
        
        # Start game in a separate thread
        self.game_thread = threading.Thread(target=self.run_game)
        self.game_thread.daemon = True
        self.game_thread.start()
    
    def start_ollama_server(self):
        """Start the Ollama server in a separate process"""
        try:
            # Check if Ollama is already running
            subprocess.run(['pgrep', 'ollama'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Start Ollama server
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            # Wait for server to start
            time.sleep(2)
    
    def reset_game(self):
        """Reset the current game"""
        self.is_running = False
        if self.game_process:
            try:
                self.game_process.stdin.write(b'quit\n')
                self.game_process.stdin.flush()
                self.game_process.stdin.write(b'y\n')
                self.game_process.stdin.flush()
                self.game_process.terminate()
                self.game_process = None
            except:
                pass
        
        # Clear the display and reset buttons
        self.text_display.clear()
        self.start_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        
        # Stop the output timer temporarily
        self.output_timer.stop()
        # Clear any remaining items in the queue
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except:
                break
        # Restart the output timer
        self.output_timer.start(100)
    
    def quit_game(self):
        """Quit the game and close the window"""
        self.is_running = False
        if self.game_process:
            try:
                self.game_process.stdin.write(b'quit\n')
                self.game_process.stdin.flush()
                self.game_process.stdin.write(b'y\n')
                self.game_process.stdin.flush()
                self.game_process.terminate()
                self.game_process = None
            except:
                pass
        QApplication.quit()
    
    def run_game(self):
        """Run the game in a separate thread"""
        try:
            # Start the game process with both 'standard in' and 'standard out' pipes
            game_file = os.path.join('games', self.game_combo.currentText())
            if not os.path.exists(game_file):
                self.output_queue.put("Error: Game file not found")
                return
                
            self.game_process = subprocess.Popen(
                ['./frotz/dfrotz', game_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                preexec_fn=None  # Disable signal handling
            )
            
            # Create output queue and thread
            output_queue = Queue()
            def enqueue_output(pipe, queue):
                for line in iter(pipe.readline, b''):
                    queue.put(line.decode('utf-8', errors='ignore'))
                pipe.close()
            
            output_thread = threading.Thread(target=enqueue_output, args=(self.game_process.stdout, output_queue))
            output_thread.daemon = True
            output_thread.start()
            
            # Get initial game output
            def get_output():
                output = ''
                while True:
                    try:
                        line = output_queue.get_nowait()
                        # Filter out score and moves information
                        if not any(x in line for x in ['Score:', 'Moves:', 'Score: 0', 'Moves: 0']):
                            output += line
                    except:
                        break
                return output.replace('\n', ' ').replace('>', ' ').replace('<', ' ').strip()
            
            # Get start info
            start_output = get_output()
            if 'Press' in start_output or 'press' in start_output or 'Hit' in start_output or 'hit' in start_output:
                self.game_process.stdin.write(b' \n')
                self.game_process.stdin.flush()
                start_output += get_output()
            if 'introduction' in start_output:
                self.game_process.stdin.write(b'no\n')
                self.game_process.stdin.flush()
                start_output += get_output()
            
            self.output_queue.put(start_output)
            
            # Initialize game history with a maximum size
            game_history = []
            last_action_time = 0
            
            while self.is_running:
                current_time = time.time()
                
                # Wait at least 0.5 seconds between actions
                if current_time - last_action_time >= 0.5:
                    # Get AI's next action, only using the last 5 actions for context
                    thinking, action = chat_with_ollama(start_output, "\n".join(game_history[-5:]))
                    
                    if thinking and action:
                        # Send the action to the game
                        self.game_process.stdin.write((action + '\n').encode())
                        self.game_process.stdin.flush()
                        
                        # Get game output
                        game_output = get_output()
                        self.output_queue.put(f"\n{game_output}\n")
                        self.output_queue.put(f"\nThinking...\n")
                        
                        # Use the configured wait time
                        time.sleep(self.current_wait_time)
                        
                        # Show AI's reasoning and action
                        self.output_queue.put(f"AI Reasoning: {thinking}\n")
                        self.output_queue.put(f"> {action}\n\n")
                        
                        # Add action to history and maintain size limit
                        game_history.append(action)
                        if len(game_history) > self.max_history_size:
                            game_history.pop(0)  # Remove oldest action
                        
                        start_output = game_output
                        last_action_time = current_time
                    
                    # Check for quit command
                    if action and action.lower().strip() == 'quit':
                        self.game_process.stdin.write(b'quit\n')
                        self.game_process.stdin.flush()
                        self.game_process.stdin.write(b'y\n')
                        self.game_process.stdin.flush()
                        break
                        
        except Exception as e:
            self.output_queue.put(f"Error running game: {e}")
            if self.game_process:
                try:
                    self.game_process.terminate()
                    self.game_process = None
                except:
                    pass

def chat_with_ollama(game_output, game_history):
    """
    Send game output to Ollama and get the next action.
    """
    url = "http://localhost:11434/api/chat"
    
    # Create a context-aware prompt
    prompt = f"""You are playing Zork, a text adventure game. Here is the current game output:

{game_output}

Previous actions taken:
{game_history}

General Instructions:
- If something doesn't work, try alternate approaches or move on to something else.
- Don't say "AGAIN" in your commands, just say the command.
- Explore the game.
- If the game says you can't do something or that it doesn't understand, don't try to do it again.

ACTION syntax rules:
- Commands are in plain English, using imperative sentences
- Directions can be abbreviated: N, S, E, W, NE, NW, SE, SW, U, D
- Use "ALL" to refer to every visible object
- Multiple commands can be chained with "THEN" or "."
- Basic commands: LOOK (L), INVENTORY (I)

Think about what you should do next and why. Then take an action.

Format your response exactly like this:
THINKING: [reasoning]
ACTION: [command]

Example:
THINKING: I see a sword on the ground. Taking it would be useful for combat later.
ACTION: take sword"""

    data = {
        "model": "llama3",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        content = response.json()["message"]["content"].strip()
        
        # Parse thinking and action
        thinking = ""
        action = ""
        
        for line in content.split('\n'):
            if line.startswith('THINKING:'):
                thinking = line[9:].strip()
            elif line.startswith('ACTION:'):
                action = line[7:].strip()
        
        return thinking, action
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None, None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 