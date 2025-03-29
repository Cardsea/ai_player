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
    url = "http://localhost:11434/api/generate"

    # Create a context-aware prompt
    prompt = f"""You are playing Zork, a text adventure game.

Reminders:
- If something doesn't work, try alternate approaches or move on to something else.
- Don't repeat the same command if the results are the same.
- It's ok to get frustrated. When you do, step away and try something else.
- If you find something cool, make note of it.
- If the game doesn't understand you, try to say it more simply.
- Use concise commands.

ACTION are in plain English, using imperative sentences
ACTION Examples:
> NORTH
> EAST
> SOUTH
> WEST
> NORTHEAST
> NORTHWEST
> SOUTHEAST
> SOUTHWEST
> UP
> DOWN
> TAKE THE BIRDCAGE
> OPEN THE PANEL
> READ ABOUT DIMWIT FLATHEAD
> HIT THE LAMP
> LIE DOWN IN THE PINK SOFA
> EXAMINE THE SHINY COIN
> PUT THE RUSTY KEY IN THE CARDBOARD BOX
> SHOW MY BOW TIE TO THE BOUNCER
> HIT THE CRAWLING CRAB WITH THE GIANT NUTCRACKER
> ASK THE COWARDLY KING ABOUT THE CROWN JEWELS
> TAKE THE BOOK AND THE FROG
> DROP THE JAR OF PEANUT BUTTER, THE SPOON, AND THE LEMMING FOOD
> PUT THE EGG AND THE PENCIL IN THE CABINET
> TURN ON THE LIGHT. KICK THE LAMP.
> EXAMINE THE APPLE. TAKE IT. EAT IT
> CLOSE THE HEAVY METAL DOOR. LOCK IT
> PICK UP THE GREEN Boor. SMELL IT. PUT IT ON.
> TAKE ALL
> TAKE ALL THE TOOLS
> DROP ALL THE TOOLS EXCEPT THE WRENCH AND THE MINIATURE HAMMER
> TAKE ALL FROM THE CARTON
> GIVE ALL BUT THE RUBY SLIPPERS TO THE WICKED WITCH
> SALESMAN, HELLO
> HORSE, WHERE IS YOUR SADDLE?
> BOY, RUN HOME THEN CALL THE POLICE
> MIGHTY WIZARD, TAKE THIS POISONED APPLE. EAT IT

Conversation history:
{game_history}
game: {game_output}

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
        print(f"\n{Fore.RED}Error communicating with Ollama: {e}{Style.RESET_ALL}")
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
    finally:
        # Ensure TextPlayer is properly cleaned up
        if text_player:
            text_player.quit()

def check_ollama_connection():
    """
    Check if Ollama is running and the llama3.2 model is installed.
    Returns True if everything is ready, False otherwise.
    """
    try:
        model_check = requests.get("http://localhost:11434/api/tags")
        model_check.raise_for_status()
        models = model_check.json().get("models", [])
        if not any(model.get("name", "").startswith("llama3.2") for model in models):
            print(f"\n{Fore.RED}Error: The llama3.2 model is not installed.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}To fix this:{Style.RESET_ALL}")
            print("1. Make sure Ollama is running (ollama serve)")
            print("2. In a separate terminal, run: ollama pull llama3.2")
            print("3. Then try running this script again\n")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n{Fore.RED}Error: Could not connect to Ollama. Please make sure Ollama is installed and running.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}To fix this:{Style.RESET_ALL}")
        print("1. Install Ollama from https://ollama.com/download")
        print("2. Start Ollama by running: ollama serve")
        print("3. In a separate terminal, run: ollama pull llama3.2")
        print("4. Then try running this script again\n")
        return False

if __name__ == "__main__":
    run_zork()
