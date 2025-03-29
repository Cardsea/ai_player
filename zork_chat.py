import requests
import time
import sys
import os
from textPlayer import TextPlayer


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

Based on the game output and history, what should the player do next? Respond with ONLY the action to take (like 'look', 'north', 'take sword', etc). Do not include any explanations or additional text."""

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
        return response.json()["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def run_zork():
    print("Starting Zork...")
    print("Type 'quit' to exit the game")
    
    # Initialize TextPlayer with zork1.z5
    text_player = TextPlayer('zork1.z5')
    
    if not text_player.game_loaded_properly:
        print("Error: Failed to load zork1.z5. Make sure it's in the textplayer/games/ directory.")
        return
    
    try:
        # Get initial game output
        game_output = text_player.run()
        print(game_output)
        
        game_history = []
        last_action_time = 0
        
        while True:
            current_time = time.time()
            
            # Wait at least 0.5 seconds between actions
            if current_time - last_action_time >= 0.5:
                print("\nThinking...", end='', flush=True)
                # Get AI's next action
                action = chat_with_ollama(game_output, "\n".join(game_history[-5:]))
                
                if action:
                    print(f"\nAI Action: {action}")
                    # Send the action to the game
                    game_output = text_player.execute_command(action)
                    print(game_output)
                    game_history.append(action)
                    last_action_time = current_time
                
                # Check for quit command
                if action and action.lower().strip() == 'quit':
                    text_player.quit()
                    break
                
    except Exception as e:
        print(f"Error running Zork: {e}")
        text_player.quit()

if __name__ == "__main__":
    run_zork() 