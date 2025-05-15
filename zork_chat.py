import requests
import time
import os
from textPlayer import TextPlayer
from colorama import init, Fore, Style
import json
import re

# Initialize colorama
init()

# Save file location
SAVE_FILE = "zorkgame.sav"

def is_movement_command(command):
    """
    Check if the command is a movement direction.
    """
    directions = ["n", "north", "s", "south", "e", "east", "w", "west", "up", "down", "ne", "northwest", "se", "southeast", "sw", "southwest", "nw", "northeast"]
    return command.lower().strip() in directions

def extract_room_name(output):
    """
    Extract the room name from the game output.
    """
    # Look for text before the first newline or the whole string if no newline
    first_line = output.split("\n")[0].strip()

    # Check if it's likely a room name (starts with capital letter and not an error message)
    if first_line and first_line[0].isupper() and "I don't understand" not in first_line and "I can't" not in first_line:
        return first_line

    # If no room name found, check for common room name patterns
    room_pattern = re.search(r"(You are in|You're in|This is) (the )?(.*?)(\.|$)", output)
    if room_pattern:
        return room_pattern.group(3).strip()

    return None

def save_game(text_player):
    """
    Save the current game state to a file.
    Returns the output from the save command, or None if it failed.
    """
    print(f"{Fore.YELLOW}Auto-saving game...{Style.RESET_ALL}", flush=True)
    # Execute the save command
    save_output = text_player.execute_command("save")

    # Check if the command prompted for a filename
    if "Please enter a filename" in save_output or "file name" in save_output.lower():
        # If prompted for filename, provide it and capture the new output
        filename_output = text_player.execute_command(SAVE_FILE)
        # Use only the output after providing the filename for success check
        save_output += '\n' + filename_output
        final_output = filename_output
    else:
        final_output = save_output

    # Check if save was successful in the final output
    if "Ok." in final_output or "Saved" in final_output or "saved" in final_output.lower():
        print(f"{Fore.GREEN}Game saved successfully!{Style.RESET_ALL}", flush=True)
        return save_output
    else:
        print(f"{Fore.RED}Failed to save game: {save_output}{Style.RESET_ALL}", flush=True)
        return None

def load_game(text_player):
    """
    Load a saved game state from a file.
    Returns the output from the restore command, or None if it failed.
    """
    # Check if save file exists
    if not os.path.exists(SAVE_FILE):
        print(f"{Fore.YELLOW}No save file found at {SAVE_FILE}{Style.RESET_ALL}", flush=True)
        return None

    print(f"{Fore.YELLOW}Loading saved game...{Style.RESET_ALL}", flush=True)
    # Execute the restore command - use double quotes around filename
    restore_output = text_player.execute_command("restore")

    # Check if the command prompted for a filename
    if "Please enter a filename" in restore_output or "file name" in restore_output.lower():
        # If prompted for filename, provide it
        restore_output += text_player.execute_command(SAVE_FILE)

    # Check if restore was successful
    if "Ok." in restore_output or "Restored" in restore_output or "restored" in restore_output.lower():
        print(f"{Fore.GREEN}Game loaded successfully!{Style.RESET_ALL}", flush=True)
        return restore_output
    else:
        print(f"{Fore.RED}Failed to load game: {restore_output}{Style.RESET_ALL}", flush=True)
        return None

def evaluate_progress(game_history, current_output, movement_history):
    """
    Evaluate the current game progress and create/update goals and plans.
    Returns a goal, plan, and reasoning for next actions.
    """
    url = "http://localhost:11434/api/chat"

    system_prompt = """
You are playing Zork I. Your job is to analyze the current game state
and develop a clear goal and plan based on what has been discovered so far.

Focus on identifying:
1. Current location and notable objects
2. Key achievements so far
3. Current obstacles or puzzles
4. Most logical next steps
5. Critique of the past actions, supplying corrective goals if needed

Be concise and clear. Avoid speculation and focus on concrete facts from the game.
"""

    # Create a condensed history for the evaluator to work with
    condensed_history = []
    for entry in game_history[-20:]:  # Use the last 20 entries to avoid overwhelming the evaluator
        condensed_history.append(entry)

    # Format movement history into a readable path
    movement_path = "Movement path: "
    if movement_history:
        for i, move in enumerate(movement_history[-20:]):  # Only show the last 20 movements
            movement_path += f"[{move['from']} -> {move['direction']} -> {move['to']}]"
            if i < len(movement_history[-20:]) - 1:
                movement_path += " → "
    else:
        movement_path += "No movements recorded yet."

    # Add the current output with movement history
    user_prompt = f"""
    Based on the game history and current output, please provide:
    1. A clear current goal
    2. A concrete plan for the next 3-5 steps
    3. Brief reasoning for your assessment
    4. Critique of the past actions

    Current game output: {current_output}
    {movement_path}
    """

    condensed_history.append({
        "role": "user",
        "content": f"Based on the game history and current output, please provide:\n1. A clear current goal\n2. A concrete plan for the next 3-5 steps\n3. Brief reasoning for your assessment\n\nCurrent game output: {current_output}\n\n{movement_path}"
    })

    data = {
        "model": "llama3.2",
        "messages": [
            {"role": "system", "content": system_prompt},
            *condensed_history
        ],
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "goal": {
                    "description": "The current main goal in the game",
                    "type": "string"
                },
                "plan": {
                    "description": "A clear plan for the next few steps",
                    "type": "string"
                },
                "reasoning": {
                    "description": "Brief reasoning for the goal and plan",
                    "type": "string"
                },
                "critique": {
                    "description": "Critique of the past actions",
                    "type": "string"
                }
            },
            "required": [
                "goal",
                "plan",
                "reasoning",
                "critique"
            ]
        },
        "options": {
            "temperature": 0.5
        }
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        content = response.json()["message"]["content"].strip()
        try:
            result = json.loads(content)
            goal = result.get("goal", "Explore the current area")
            plan = result.get("plan", "Look around, examine objects, and try to find useful items")
            reasoning = result.get("reasoning", "Need to gather more information about the environment")
            critique = result.get("critique", "No critique provided")
            return goal, plan, reasoning, critique
        except json.JSONDecodeError:
            return "Explore the current area", "Look around, examine objects, and try to find useful items", "Need to gather more information about the environment"

    except requests.exceptions.RequestException:
        return "Explore the current area", "Look around, examine objects, and try to find useful items", "Need to gather more information about the environment"

def chat_with_ollama(game_output, game_history, goal, plan, reasoning, critique, movement_history):
    """
    Send game output to Ollama and get the next action.
    """
    url = "http://localhost:11434/api/chat"

    # Format movement history into a readable path for the last 5 movements
    movement_path = ""
    if movement_history:
        movement_path = "Recent movement path: "
        for i, move in enumerate(movement_history[-5:]):  # Only show the last 5 movements
            movement_path += f"[{move['from']} -> {move['direction']} -> {move['to']}]"
            if i < len(movement_history[-5:]) - 1:
                movement_path += " → "

    # Create a context-aware prompt
    system_prompt = f"""
You are a player playing Zork I.
You are trying to solve the puzzles and navigate the world.
There is a lot to discover, try to find everything you can.

GOAL: {goal}
PLAN: {plan}
REASONING: {reasoning}
CRITIQUE: {critique}

{movement_path}

DON'T GIVE UP! ZORK IS A HARD GAME BUT IT IS SOLVABLE!

Reminders:
- Be concise.
- If something doesn't work or you get lost, try the LOOK and EXITS commands to get your bearings.
- If you get stuck trying exploring in different directions.
- Direction ACTIONs: EXITS, N, E, S, W, UP, DOWN, NE, SE, SW, NW
- Common ACTIONs: LOOK, EXAMINE, INVENTORY, TAKE, DROP, OPEN, USE
- Other ACTIONs: READ, HIT, PUT _ IN _, SHOW _ TO _, GIVE _ TO _, DROP _, WAIT

DO NOT QUIT!

"""
# You must respond with a JSON object. Example:
# { "thinking": "I see a sword on the ground. Taking it would be useful for combat later.", "action": "take sword" }

    # Create messages array with system prompt and game history
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(game_history)
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
    MAX_HISTORY = 30  # Number of turns to keep in history
    AUTOSAVE_INTERVAL = 10000000 # disabled  # Auto-save every 20 steps

    last_action_time = 0
    failure_count = 0
    steps = 0
    game_history = []
    evaluation_counter = 0
    current_goal = "Explore the starting area"
    current_plan = "Look around, examine objects, and try to gather useful items"
    current_reasoning = "Need to gather information about the starting location"
    current_critique = "Approach is fine so far."
    # Room tracking
    movement_history = []
    current_room = "Unknown"

    # Get initial game output
    game_output = text_player.run()
    room_name = extract_room_name(game_output)
    if room_name:
        current_room = room_name
        print(f"{Fore.YELLOW}Starting in: {current_room}{Style.RESET_ALL}")

    game_history.append({"role": "user", "content": game_output})
    print(f"{Fore.GREEN}{game_output}{Style.RESET_ALL}")

    # Try to load a saved game if one exists
    load_output = load_game(text_player)
    if load_output:
        # Get the updated room after loading
        game_output = text_player.execute_command("look")
        room_name = extract_room_name(game_output)
        if room_name:
            current_room = room_name
            print(f"{Fore.YELLOW}Current location: {current_room}{Style.RESET_ALL}")
        game_history.append({"role": "user", "content": game_output})
        print(f"{Fore.GREEN}{game_output}{Style.RESET_ALL}")

    while True:
        current_time = time.time()

        # Wait at least 0.5 seconds between actions
        if current_time - last_action_time >= 0.5:
            # Auto-save every AUTOSAVE_INTERVAL steps
            if steps > 0 and steps % AUTOSAVE_INTERVAL == 0:
                save_game(text_player)

            # Evaluate progress every 5 steps
            if evaluation_counter >= 10:
                print(f"\n{Fore.YELLOW}   Evaluating progress... {Style.RESET_ALL}", flush=True)
                current_goal, current_plan, current_reasoning, current_critique = evaluate_progress(game_history, game_output, movement_history)
                print(f"{Fore.CYAN}GOAL: {current_goal}{Style.RESET_ALL}", flush=True)
                print(f"{Fore.CYAN}PLAN: {current_plan}{Style.RESET_ALL}", flush=True)
                print(f"{Fore.CYAN}REASONING: {current_reasoning}{Style.RESET_ALL}\n", flush=True)
                print(f"{Fore.CYAN}CRITIQUE: {current_critique}{Style.RESET_ALL}\n", flush=True)

                # Print movement history
                if movement_history:
                    print(f"{Fore.YELLOW}MOVEMENT PATH (last 5):{Style.RESET_ALL}", flush=True)
                    for i, move in enumerate(movement_history[-5:]):
                        print(f"{Fore.YELLOW}  {move['from']} → {move['direction']} → {move['to']}{Style.RESET_ALL}", flush=True)
                    print()

                evaluation_counter = 0

            # Show thinking indicator
            print(f"\n{Fore.YELLOW}   Thinking... {Style.RESET_ALL}", end='', flush=True)

            # Get AI's next action
            thinking, action = chat_with_ollama(game_output, game_history, current_goal, current_plan, current_reasoning, current_critique, movement_history)

            if thinking or action:
                failure_count = 0
                # Show AI's reasoning and action
                print(f"{Fore.BLUE}{thinking}{Style.RESET_ALL}", flush=True)
                print(f"{Fore.MAGENTA}{steps}> {action}{Style.RESET_ALL}", flush=True)
                print("\n")

                # Record the current room before executing command
                previous_room = current_room

                # Send the action to the game
                game_output = text_player.execute_command(action)

                # Check if this was a movement command and update room tracking
                if is_movement_command(action):
                    new_room_name = extract_room_name(game_output)
                    if new_room_name and new_room_name != current_room:
                        # Record the movement in our history
                        movement = {
                            "from": previous_room,
                            "direction": action,
                            "to": new_room_name
                        }
                        movement_history.append(movement)
                        current_room = new_room_name
                        print(f"{Fore.YELLOW}Moved to: {current_room}{Style.RESET_ALL}", flush=True)

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
                evaluation_counter += 1
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
                # Save game before quitting
                save_game(text_player)
                return False

    return True

def run_zork():
    print(f"{Fore.CYAN}Starting Zork...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Type 'quit' to exit the game{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Game will auto-save every 20 steps and when quitting{Style.RESET_ALL}")

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
