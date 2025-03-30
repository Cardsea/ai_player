import requests
import time
import os
from textPlayer import TextPlayer
import random
from colorama import init, Fore, Style
import tkinter as tk
from tkinter import scrolledtext, colorchooser, ttk
import threading
from queue import Queue
import subprocess

# Initialize colorama
init()

class CustomThemeWindow:
    def __init__(self, parent, app):
        self.window = tk.Toplevel(parent)
        self.window.title("Custom Theme")
        self.window.geometry("400x600")
        self.app = app
        
        # Create main frame
        main_frame = tk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Color settings
        self.colors = {
            'window_bg': tk.StringVar(value=app.window_bg),
            'text_bg': tk.StringVar(value=app.text_bg),
            'text_fg': tk.StringVar(value=app.text_fg),
            'thinking_color': tk.StringVar(value=app.thinking_color),
            'ai_response_color': tk.StringVar(value=app.ai_response_color),
            'game_output_color': tk.StringVar(value=app.game_output_color),
            'button_bg': tk.StringVar(value=app.button_bg),
            'button_fg': tk.StringVar(value=app.button_fg),
            'button_active_bg': tk.StringVar(value=app.button_active_bg),
            'button_active_fg': tk.StringVar(value=app.button_active_fg)
        }
        
        # Create color pickers
        self.create_color_picker(main_frame, "Window Background", self.colors['window_bg'])
        self.create_color_picker(main_frame, "Text Background", self.colors['text_bg'])
        self.create_color_picker(main_frame, "Text Color", self.colors['text_fg'])
        self.create_color_picker(main_frame, "'Thinking' Text Color", self.colors['thinking_color'])
        self.create_color_picker(main_frame, "AI Response Color", self.colors['ai_response_color'])
        self.create_color_picker(main_frame, "Game Output Color", self.colors['game_output_color'])
        self.create_color_picker(main_frame, "Button Background", self.colors['button_bg'])
        self.create_color_picker(main_frame, "Button Text Color", self.colors['button_fg'])
        self.create_color_picker(main_frame, "Button Active Background", self.colors['button_active_bg'])
        self.create_color_picker(main_frame, "Button Active Text Color", self.colors['button_active_fg'])
        
        # Preview button
        preview_button = tk.Button(
            main_frame,
            text="Preview Theme",
            command=self.preview_theme
        )
        preview_button.pack(pady=10)
        
        # Save button
        save_button = tk.Button(
            main_frame,
            text="Save Theme",
            command=self.save_theme
        )
        save_button.pack(pady=10)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
    
    def create_color_picker(self, parent, label, color_var):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(frame, text=label).pack(side=tk.LEFT)
        
        # Create color preview
        preview = tk.Frame(frame, width=30, height=20, bg=color_var.get())
        preview.pack(side=tk.RIGHT, padx=5)
        
        def choose_color():
            color = colorchooser.askcolor(color=color_var.get(), title=f"Choose {label}")[1]
            if color:
                color_var.set(color)
                preview.configure(bg=color)
        
        tk.Button(frame, text="Choose", command=choose_color).pack(side=tk.RIGHT)
    
    def preview_theme(self):
        """Apply the current color settings as a preview"""
        self.app.apply_custom_theme(self.colors)
    
    def save_theme(self):
        """Save the custom theme and close window"""
        self.app.save_custom_theme(self.colors)
        self.window.destroy()

class SettingsWindow:
    def __init__(self, parent, app):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x600")
        self.app = app
        
        # Create main frame with scrollbar
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Game Settings Section
        game_frame = tk.LabelFrame(scrollable_frame, text="Game Settings", padding="10")
        game_frame.pack(fill=tk.X, pady=5)
        
        # Wait time control
        wait_frame = tk.Frame(game_frame)
        wait_frame.pack(fill=tk.X, pady=5)
        wait_label = tk.Label(wait_frame, text="AI Thinking Time (seconds):", font=('Helvetica', 12))
        wait_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.wait_time = tk.DoubleVar(value=app.current_wait_time)
        wait_scale = tk.Scale(
            wait_frame,
            from_=0.5,
            to=5.0,
            orient=tk.HORIZONTAL,
            variable=self.wait_time,
            command=self.update_wait_time
        )
        wait_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        wait_value = tk.Label(wait_frame, textvariable=self.wait_time, font=('Helvetica', 12))
        wait_value.pack(side=tk.LEFT)
        
        # History size control
        history_frame = tk.Frame(game_frame)
        history_frame.pack(fill=tk.X, pady=5)
        history_label = tk.Label(history_frame, text="Game History Size:", font=('Helvetica', 12))
        history_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.history_size = tk.IntVar(value=app.max_history_size)
        history_scale = tk.Scale(
            history_frame,
            from_=5,
            to=20,
            orient=tk.HORIZONTAL,
            variable=self.history_size,
            command=self.update_history_size
        )
        history_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        history_value = tk.Label(history_frame, textvariable=self.history_size, font=('Helvetica', 12))
        history_value.pack(side=tk.LEFT)
        
        # Display Settings Section
        display_frame = tk.LabelFrame(scrollable_frame, text="Display Settings", padding="10")
        display_frame.pack(fill=tk.X, pady=5)
        
        # Font size control
        font_frame = tk.Frame(display_frame)
        font_frame.pack(fill=tk.X, pady=5)
        font_label = tk.Label(font_frame, text="Text Size:", font=('Helvetica', 12))
        font_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.font_size = tk.IntVar(value=app.font_size)
        font_scale = tk.Scale(
            font_frame,
            from_=10,
            to=20,
            orient=tk.HORIZONTAL,
            variable=self.font_size,
            command=self.update_font_size
        )
        font_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        font_value = tk.Label(font_frame, textvariable=self.font_size, font=('Helvetica', 12))
        font_value.pack(side=tk.LEFT)
        
        # AI Settings Section
        ai_frame = tk.LabelFrame(scrollable_frame, text="AI Settings", padding="10")
        ai_frame.pack(fill=tk.X, pady=5)
        
        # Model selection
        model_frame = tk.Frame(ai_frame)
        model_frame.pack(fill=tk.X, pady=5)
        model_label = tk.Label(model_frame, text="AI Model:", font=('Helvetica', 12))
        model_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_var = tk.StringVar(value=app.ai_model)
        models = ['llama3', 'mistral', 'codellama']
        model_combo = tk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=models,
            state="readonly",
            width=15
        )
        model_combo.pack(side=tk.LEFT)
        
        # Temperature control
        temp_frame = tk.Frame(ai_frame)
        temp_frame.pack(fill=tk.X, pady=5)
        temp_label = tk.Label(temp_frame, text="AI Creativity:", font=('Helvetica', 12))
        temp_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.temperature = tk.DoubleVar(value=app.ai_temperature)
        temp_scale = tk.Scale(
            temp_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.temperature,
            command=self.update_temperature
        )
        temp_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        temp_value = tk.Label(temp_frame, textvariable=self.temperature, font=('Helvetica', 12))
        temp_value.pack(side=tk.LEFT)
        
        # Save button
        save_button = tk.Button(
            scrollable_frame,
            text="Save Settings",
            command=self.save_settings
        )
        save_button.pack(pady=20)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
    
    def update_wait_time(self, *args):
        """Update the wait time value display"""
        self.wait_time.set(self.wait_time.get())
    
    def update_history_size(self, *args):
        """Update the history size value display"""
        self.history_size.set(self.history_size.get())
    
    def update_font_size(self, *args):
        """Update the font size value display"""
        self.font_size.set(self.font_size.get())
    
    def update_temperature(self, *args):
        """Update the temperature value display"""
        self.temperature.set(self.temperature.get())
    
    def save_settings(self):
        """Save settings and close window"""
        self.app.current_wait_time = self.wait_time.get()
        self.app.max_history_size = self.history_size.get()
        self.app.font_size = self.font_size.get()
        self.app.ai_model = self.model_var.get()
        self.app.ai_temperature = self.temperature.get()
        
        # Apply font size
        self.app.text_display.configure(font=('Helvetica', self.app.font_size))
        
        self.window.destroy()

class ZorkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text Adventure AI Player")
        self.root.geometry("1200x800")
        
        # Initialize settings
        self.current_wait_time = 1.0
        self.max_history_size = 10
        self.font_size = 14
        self.ai_model = 'llama3'
        self.ai_temperature = 0.7
        
        # Set up colors
        self.window_bg = '#1A1A1A'  # Soft black
        self.text_bg = '#1A1A1A'    # Same as window
        self.text_fg = '#E0E0E0'    # Soft white
        self.thinking_color = '#D4B483'  # Dark yellow
        self.ai_response_color = '#9B6B9E'  # Dark purple
        self.game_output_color = '#7A9B7A'  # Dark green
        
        # Configure root window
        self.root.configure(bg=self.window_bg)
        self.root.option_add('*Font', 'Helvetica 12')
        
        # Configure ttk styles
        style = ttk.Style()
        style.configure('TFrame', background=self.window_bg)
        style.configure('TLabel', background=self.window_bg, foreground=self.text_fg)
        style.configure('TButton', 
                       background=self.window_bg,
                       foreground=self.text_fg,
                       padding=5)
        style.configure('TCombobox',
                       fieldbackground=self.window_bg,
                       background=self.window_bg,
                       foreground=self.text_fg,
                       selectbackground=self.ai_response_color,
                       selectforeground=self.text_fg)
        style.configure('TScale',
                       background=self.window_bg,
                       foreground=self.text_fg)
        style.configure('TLabelframe',
                       background=self.window_bg,
                       foreground=self.text_fg)
        style.configure('TLabelframe.Label',
                       background=self.window_bg,
                       foreground=self.text_fg)
        
        # Make window resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame with padding and background
        main_frame = ttk.Frame(root, padding=20)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # Create title banner
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame,
            text="Text Adventure AI Player",
            font=('Helvetica', 32, 'bold')
        )
        title_label.pack()
        
        # Create game selector
        selector_frame = ttk.Frame(main_frame)
        selector_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.game_var = tk.StringVar()
        self.game_var.set("zork1.z5")  # Default game
        game_label = ttk.Label(selector_frame, text="Select Game:", font=('Helvetica', 14))
        game_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Get list of games
        self.games = [f for f in os.listdir('games') if f.endswith('.z5')]
        self.games.sort()
        game_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.game_var,
            values=self.games,
            state="readonly",
            width=40,
            font=('Helvetica', 12)
        )
        game_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.E), pady=(0, 10))
        
        # Create control buttons
        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            command=self.start_game
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self.reset_game,
            state=tk.DISABLED
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.settings_button = ttk.Button(
            button_frame,
            text="Settings",
            command=self.open_settings
        )
        self.settings_button.pack(side=tk.LEFT, padx=5)
        
        self.quit_button = ttk.Button(
            button_frame,
            text="Quit",
            command=self.quit_game
        )
        self.quit_button.pack(side=tk.LEFT, padx=5)
        
        # Create text display area
        self.text_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            height=30,
            width=120,
            font=('Helvetica', self.font_size),
            bg=self.text_bg,
            fg=self.text_fg,
            padx=15,
            pady=15,
            selectbackground=self.ai_response_color,
            selectforeground=self.text_fg,
            insertbackground=self.text_fg
        )
        self.text_display.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Initialize game variables
        self.text_player = None
        self.game_thread = None
        self.is_running = False
        self.output_queue = Queue()
        self.game_process = None
        
        # Configure text tags
        self.text_display.tag_configure("thinking", foreground=self.thinking_color)
        self.text_display.tag_configure("ai_response", foreground=self.ai_response_color)
        self.text_display.tag_configure("game_output", foreground=self.game_output_color)
        
        # Start checking for output updates
        self.check_output_queue()
    
    def check_output_queue(self):
        """Check for new output in the queue and update the display"""
        try:
            while True:
                text = self.output_queue.get_nowait()
                if "AI Reasoning:" in text:
                    self.text_display.insert(tk.END, text + "\n", "thinking")
                elif text.startswith(">"):
                    self.text_display.insert(tk.END, text + "\n", "ai_response")
                else:
                    self.text_display.insert(tk.END, text + "\n", "game_output")
                self.text_display.see(tk.END)
                
                # Configure tags for different text types
                self.text_display.tag_configure("thinking", foreground=self.thinking_color)
                self.text_display.tag_configure("ai_response", foreground=self.ai_response_color)
                self.text_display.tag_configure("game_output", foreground=self.game_output_color)
        except:
            pass
        finally:
            self.root.after(100, self.check_output_queue)
    
    def open_settings(self):
        """Open the settings window"""
        SettingsWindow(self.root, self)
    
    def start_game(self):
        """Start a new game"""
        if self.is_running:
            return
            
        self.is_running = True
        self.start_button.state(['disabled'])
        self.reset_button.state(['!disabled'])
        
        # Clear the display
        self.text_display.delete(1.0, tk.END)
        
        # Start game in a separate thread
        self.game_thread = threading.Thread(target=self.run_game)
        self.game_thread.daemon = True
        self.game_thread.start()
    
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
        self.start_button.state(['!disabled'])
        self.reset_button.state(['disabled'])
        self.text_display.delete(1.0, tk.END)
    
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
        self.root.quit()
    
    def run_game(self):
        """Run the game in a separate thread"""
        try:
            # Start the game process with both 'standard in' and 'standard out' pipes
            game_file = os.path.join('games', self.game_var.get())
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
            MAX_HISTORY_SIZE = 10  # Keep only the last 10 actions
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
                        self.output_queue.put(f"\n{game_output}")
                        self.output_queue.put(f"\nThinking...")
                        
                        # Use the configured wait time
                        time.sleep(self.current_wait_time)
                        
                        # Show AI's reasoning and action
                        self.output_queue.put(f"AI Reasoning: {thinking}")
                        self.output_queue.put(f"> {action}\n")
                        
                        # Add action to history and maintain size limit
                        game_history.append(action)
                        if len(game_history) > MAX_HISTORY_SIZE:
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
    root = tk.Tk()
    app = ZorkGUI(root)
    root.mainloop() 