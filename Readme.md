# Text Adventure AI Player

A Python-based GUI application that uses AI to play text adventure games like Zork. The application provides a modern interface for watching an AI play through classic text adventure games.

This is a fork of [danielricks/textplayer](https://github.com/danielricks/textplayer), which is itself a fork of the original [DavidGriffith/textplayer](https://github.com/DavidGriffith/textplayer) repository. The original repository was designed for Python 2 and will not work with Python 3. This fork has been modified to work with Python 3 and includes additional AI features.

## Features

- Modern, user-friendly GUI interface
- Support for multiple text adventure games (.z5 format)
- AI-powered gameplay using Ollama
- Real-time display of game progress and AI reasoning
- Easy game selection and control
- Python 3 compatibility (original version only works with Python 2)

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally
- Text adventure game files in .z5 format

## Installation

You will need to install [Ollama](https://ollama.com/download).

After it is installed run the model you wish you use:

```bash
ollama run llama3.2
```

We also need Frotz, a Z-Machine interpreter written by Stefan Jokisch in 1995-1997. More information [here](http://frotz.sourceforge.net/).

Init submodules and then compile dfrotz

```bash
git submodule init
git submodule update # fetches https://github.com/DavidGriffith/frotz.git
cd frotz
make dfrotz # you will probably get a minor warning, it's safe to ignore.
```

Now install the python dependencies. Due to system protection on newer Python installations (especially on macOS), you must use a virtual environment:

```bash
# Create a virtual environment in the project directory
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install the required packages
python3 -m pip install -r requirements.txt
```

If you encounter any dependency conflicts, you can try installing with the `--no-deps` flag first and then install dependencies separately:

```bash
python3 -m pip install --no-deps -r requirements.txt
python3 -m pip install six
```

Remember to always activate the virtual environment before running the code:
```bash
source venv/bin/activate  # On macOS/Linux
# or
# .\venv\Scripts\activate  # On Windows
```

## Usage

Example commands are below.

```bash
python3 zork_chat.py
```

To run games interactively in the terminal, run the bash command below in the textplayer folder.

```bash
pip install -r requirements.txt
```

3. Install Ollama:
   - Visit [Ollama's website](https://ollama.ai/download) to download and install for your operating system
   - Follow the installation instructions for your specific OS

4. Start Ollama service:
```bash
ollama serve
```

5. Pull the required model:
```bash
ollama pull llama3
```

6. Place your .z5 game files in the `games` directory:
```bash
mkdir games
# Copy your .z5 game files into the games directory
```

## Running the Application

1. Ensure Ollama is running in the background:
```bash
ollama serve
```

2. Start the application:
```bash
python Main_Game_ui.py
```

3. In the GUI:
   - Select a game from the dropdown menu
   - Click "Start" to begin AI gameplay
   - Use "Reset" to restart the game
   - Click "Quit" to exit the application

## Project Structure

```
ai_player/
├── Main_Game_ui.py    # Main GUI application
├── textPlayer.py      # Core game interaction logic
├── requirements.txt   # Python dependencies
├── games/            # Directory for .z5 game files
└── frotz/            # Frotz interpreter for running games
```

## Troubleshooting

1. If Ollama connection fails:
   - Ensure Ollama service is running (`ollama serve`)
   - Check if the model is downloaded (`ollama list`)
   - Verify the Ollama API is accessible at http://localhost:11434

2. If games don't load:
   - Verify .z5 files are present in the `games` directory
   - Check file permissions
   - Ensure Frotz interpreter is executable

3. If GUI doesn't start:
   - Verify all Python dependencies are installed
   - Check Python version (3.8+ required)
   - Note: The original repository only works with Python 2

## Credits

- Original textplayer repository by [David Griffith](https://github.com/DavidGriffith/textplayer) (Python 2 version)
- Python 2 fork by [danielricks](https://github.com/danielricks/textplayer)
- Frotz interpreter by Stefan Jokisch
- Ollama for providing the AI capabilities
- This fork has been modified for Python 3 compatibility and AI features

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
