import requests
import time
from textPlayer import TextPlayer
from colorama import init, Fore, Style
import json

# Initialize colorama
init()

def chat_with_ollama(game_output, game_history, last_look):
    """
    Send game output to Ollama and get the next action.
    """
    url = "http://localhost:11434/api/chat"

    # Create a context-aware prompt
    system_prompt = """
You are a player playing Zork I.
You are trying to solve the puzzles and navigate the world.
There is a lot to discover, try to find everything you can.

DON'T GIVE UP! ZORK IS A HARD GAME BUT IT IS SOLVABLE!

Reminders:
- Be concise.
- If something doesn't work, don't repeat the same command.
- If you get lost, try going back the way you came.
- Direction ACTIONs: EXITS, N, E, S, W, UP, DOWN, NE, SE, SW, NW
- Common ACTIONs: LOOK, EXAMINE, INVENTORY, TAKE, DROP, OPEN, USE
- Other ACTIONs: READ, HIT, PUT _ IN _, SHOW _ TO _, GIVE _ TO _, DROP _, WAIT
- COMBINE items with AND.
- If you get stuck, LOOK, EXAMINE, and MOVE TO A NEW ROOM!

DO NOT GIVE UP!

Ask yourself what would you do next to find your way. Make a plan and then take an action.

"""
# You must respond with a JSON object. Example:
# { "thinking": "I see a sword on the ground. Taking it would be useful for combat later.", "action": "take sword" }

    # Create messages array with system prompt and game history
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(game_history)
    # messages.append({"role": "user", "content": last_look}) if last_look and last_look != game_output else None
    messages.append({"role": "user", "content": game_output})

    data = {
        "model": "llama3.2",
        "messages": messages,
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "thinking": {
                    "description": "A string explaining your reasoning",
                    "type": "string"
                },
                "action": {
                    "description": "A string with the command to execute",
                    "type": "string"
                }
            },
            "required": [
                "thinking",
                "action"
            ]
        },
        "options": {
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        # Get the content from the response
        content = response.json()["message"]["content"].strip()

        # Parse the JSON response
        try:
            result = json.loads(content)
            thinking = result.get("thinking", "")
            action = result.get("action", "")
            action = clean_action(action)
        except json.JSONDecodeError as e:
            print(f"\n{Fore.RED}Error parsing AI response as JSON: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}Raw response was:\n{content}{Style.RESET_ALL}")
            return None, None

        # If we got nothing, print out the full response for debugging
        if not thinking or not action:
            print(f"\n{Fore.RED}Debug: Got empty response. Full response was:\n{content}{Style.RESET_ALL}")

        return thinking, action
    except requests.exceptions.RequestException as e:
        print(f"\n{Fore.RED}Error communicating with Ollama: {e}{Style.RESET_ALL}")
        return None, None

def clean_action(action):
    """
    The AI loves to say certain patterns of words that are not valid commands.
    This function removes those patterns.
    """
    action = action.strip()
    action = action.lower()
    action = action.replace("look around", "look")
    action = action.replace("more", "")
    action = action.replace("again", "")
    action = action.replace("more closely", "")
    action = action.replace("try", "")
    if action == "":
        return "look"
    else:
        return action.strip()

def run_game_loop(text_player):
    """
    Run the main game loop, handling AI interactions and game state.
    Returns True if the game should continue, False if it should end.
    """
    MAX_HISTORY = 20  # Number of turns to keep in history
    last_action_time = 0
    failure_count = 0
    steps = 0
    last_look = ""
    game_history = []

    # Get initial game output
    game_output = text_player.run()
    game_history.append({"role": "user", "content": game_output})
    print(f"{Fore.GREEN}{game_output}{Style.RESET_ALL}")

    while True:
        current_time = time.time()

        # Wait at least 0.5 seconds between actions
        if current_time - last_action_time >= 0.5:
            # Show thinking indicator
            print(f"\n{Fore.YELLOW}   Thinking... {Style.RESET_ALL}", end='', flush=True)

            # Get AI's next action
            thinking, action = chat_with_ollama(game_output, game_history, last_look)

            if thinking or action:
                failure_count = 0
                # Show AI's reasoning and action
                print(f"{Fore.BLUE}{thinking}{Style.RESET_ALL}", flush=True)
                print(f"{Fore.MAGENTA}{steps}> {action}{Style.RESET_ALL}", flush=True)
                print("\n")

                # Send the action to the game
                game_output = text_player.execute_command(action)

                # Zork shortens the descriptions of rooms after the first time you look around.
                # We're going to record the current room and send it to Ollama
                # last_look = text_player.execute_command("look") if action != "look" else ""

                # Print game output
                print(f"{Fore.GREEN}{game_output}{Style.RESET_ALL}", flush=True)

                # Add the new interaction to history
                game_history.append({"role": "assistant", "content": f"Thinking: {thinking}\nAction: {action}"})
                game_history.append({"role": "user", "content": game_output})

                # Maintain fixed-size history (in pairs of turns)
                while len(game_history) > MAX_HISTORY * 2:  # *2 because each turn has user and game messages
                    game_history.pop(0)
                    game_history.pop(0)

                steps += 1
                last_action_time = current_time
            else:
                game_output = "Command not understood. Try again."
                failure_count += 1
                print(f"{Fore.YELLOW}Warning: {failure_count} failed attempts to get action from Ollama, trying again...{Style.RESET_ALL}")
                time.sleep(failure_count)
                if failure_count > 5:
                    print(f"{Fore.RED}Error: Failed to get action from Ollama{Style.RESET_ALL}")
                    return False

            # Check for quit command
            if action and action.lower().strip() == 'quit':
                return False

    return True

def run_zork():
    print(f"{Fore.CYAN}Starting Zork...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Type 'quit' to exit the game{Style.RESET_ALL}")

    # Initialize TextPlayer with zork1.z5
    text_player = None
    try:
        text_player = TextPlayer('zork1.z5')

        if not text_player.game_loaded_properly:
            print(f"{Fore.RED}Error: Failed to load zork1.z5. Make sure it's in the games/ directory.{Style.RESET_ALL}")
            return

        # Check Ollama connection first
        if not check_ollama_connection():
            return

        # Run the main game loop
        run_game_loop(text_player)

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
