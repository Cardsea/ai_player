import requests
import time
import sys
import os
from textPlayer import TextPlayer
import random
from colorama import init, Fore, Style

# Initialize colorama
init()

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

def run_zork():
    print(f"{Fore.CYAN}Starting Zork...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Type 'quit' to exit the game{Style.RESET_ALL}")
    
    # Initialize TextPlayer with zork1.z5
    text_player = TextPlayer('zork1.z5')
    
    if not text_player.game_loaded_properly:
        print(f"{Fore.RED}Error: Failed to load zork1.z5. Make sure it's in the textplayer/games/ directory.{Style.RESET_ALL}")
        return
    
    try:
        # Get initial game output
        game_output = text_player.run()
        print(f"{Fore.GREEN}{game_output}{Style.RESET_ALL}")
        
        game_history = []
        last_action_time = 0
        
        while True:
            current_time = time.time()
            
            # Wait at least 0.5 seconds between actions
            if current_time - last_action_time >= 0.5:
                # Get AI's next action
                thinking, action = chat_with_ollama(game_output, "\n".join(game_history[-5:]))
                
                if thinking and action:
                    # Send the action to the game first
                    game_output = text_player.execute_command(action)
                    # Print game output first
                    print(f"\n{Fore.GREEN}{game_output}{Style.RESET_ALL}", flush=True)
                    print(f"\n{Fore.YELLOW}   Thinking... {Style.RESET_ALL}", end='', flush=True)
                    # Add a random delay between 1-3 seconds to simulate thinking
                    time.sleep(1 + random.random())
                    # Then show AI's reasoning and action
                    print(f"{Fore.BLUE}{thinking}{Style.RESET_ALL}", flush=True)
                    print(f"{Fore.MAGENTA}   > {action}{Style.RESET_ALL}", flush=True)
                    print("\n")
                    game_history.append(action)
                    last_action_time = current_time
                
                # Check for quit command
                if action and action.lower().strip() == 'quit':
                    text_player.quit()
                    break
                
    except Exception as e:
        print(f"{Fore.RED}Error running Zork: {e}{Style.RESET_ALL}")
        text_player.quit()

if __name__ == "__main__":
    run_zork() 