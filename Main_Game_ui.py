import requests
import time
import sys
import os
from textPlayer import TextPlayer
import random
from colorama import init, Fore, Style
import tkinter as tk
from tkinter import ttk, scrolledtext, font
import threading
from queue import Queue
import subprocess

# Initialize colorama
init()

class ZorkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text Adventure AI Player")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2b2b')  # Dark background
        
        # Configure styles
        style = ttk.Style()
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff', font=('Helvetica', 10))
        style.configure('TButton', 
                       background='#3c3f41',
                       foreground='#ffffff',
                       padding=5,
                       font=('Helvetica', 10))
        style.configure('TCombobox',
                       background='#3c3f41',
                       foreground='#ffffff',
                       fieldbackground='#3c3f41',
                       selectbackground='#4b6eaf',
                       selectforeground='#ffffff')
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create game selector with custom styling
        self.game_var = tk.StringVar()
        self.game_var.set("zork1.z5")  # Default game
        game_label = ttk.Label(main_frame, text="Select Game:", font=('Helvetica', 12, 'bold'))
        game_label.grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # Get list of games
        self.games = [f for f in os.listdir('games') if f.endswith('.z5')]
        self.games.sort()
        game_combo = ttk.Combobox(main_frame, 
                                textvariable=self.game_var, 
                                values=self.games, 
                                state="readonly",
                                width=40)
        game_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=10, padx=10)
        
        # Create control buttons frame with custom styling
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=2, sticky=(tk.E), padx=10)
        
        # Create control buttons with custom styling
        self.start_button = ttk.Button(button_frame, 
                                     text="Start", 
                                     command=self.start_game,
                                     style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.reset_button = ttk.Button(button_frame, 
                                     text="Reset", 
                                     command=self.reset_game, 
                                     state=tk.DISABLED)
        self.reset_button.grid(row=0, column=1, padx=5)
        
        self.quit_button = ttk.Button(button_frame, 
                                    text="Quit", 
                                    command=self.quit_game)
        self.quit_button.grid(row=0, column=2, padx=5)
        
        # Create text display area with custom styling
        self.text_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            height=30,
            width=80,
            font=('Courier New', 12),
            bg='#1e1e1e',  # Dark background
            fg='#ffffff',  # White text
            insertbackground='#ffffff',  # White cursor
            selectbackground='#4b6eaf',  # Blue selection
            selectforeground='#ffffff',  # White selected text
            padx=10,
            pady=10
        )
        self.text_display.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Initialize game variables
        self.text_player = None
        self.game_thread = None
        self.is_running = False
        self.output_queue = Queue()
        self.game_process = None
        
        # Start checking for output updates
        self.check_output_queue()
    
    def check_output_queue(self):
        """Check for new output in the queue and update the display"""
        try:
            while True:
                text = self.output_queue.get_nowait()
                # Add different colors for different types of output
                if text.startswith("AI Reasoning:"):
                    self.text_display.insert(tk.END, text + "\n", "reasoning")
                elif text.startswith(">"):
                    self.text_display.insert(tk.END, text + "\n", "command")
                elif text.startswith("Thinking"):
                    self.text_display.insert(tk.END, text + "\n", "thinking")
                else:
                    self.text_display.insert(tk.END, text + "\n", "normal")
                self.text_display.see(tk.END)
        except:
            pass
        finally:
            self.root.after(100, self.check_output_queue)
    
    def start_game(self):
        """Start a new game"""
        if self.is_running:
            return
            
        self.is_running = True
        self.start_button.state(['disabled'])
        self.reset_button.state(['!disabled'])
        
        # Clear the display
        self.text_display.delete(1.0, tk.END)
        
        # Configure text tags for different types of output
        self.text_display.tag_configure("normal", foreground="#ffffff")
        self.text_display.tag_configure("reasoning", foreground="#4b6eaf")
        self.text_display.tag_configure("command", foreground="#6a8759")
        self.text_display.tag_configure("thinking", foreground="#cc7832")
        
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
            
            game_history = []
            last_action_time = 0
            
            while self.is_running:
                current_time = time.time()
                
                # Wait at least 0.5 seconds between actions
                if current_time - last_action_time >= 0.5:
                    # Get AI's next action
                    thinking, action = chat_with_ollama(start_output, "\n".join(game_history[-5:]))
                    
                    if thinking and action:
                        # Send the action to the game
                        self.game_process.stdin.write((action + '\n').encode())
                        self.game_process.stdin.flush()
                        
                        # Get game output
                        game_output = get_output()
                        self.output_queue.put(f"\n{game_output}")
                        self.output_queue.put(f"\nThinking...")
                        
                        # Add a random delay between 1-3 seconds to simulate thinking
                        time.sleep(1 + random.random())
                        
                        # Show AI's reasoning and action
                        self.output_queue.put(f"AI Reasoning: {thinking}")
                        self.output_queue.put(f"> {action}\n")
                        
                        game_history.append(action)
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