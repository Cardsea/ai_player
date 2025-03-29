# textplayer

This application runs a text based Z-Machine game (like Zork) and then plays it using a local install of Ollama AI much like Claude Plays Pokemon (but almost infinitely cheaper to run.)

## Requirements

You will need to install [Ollama](https://ollama.com/download).

After it is installed run the model you wish you use:

```bash
ollama run llama3.2
```

The only other requirement is Frotz, a Z-Machine interpreter written by Stefan Jokisch in 1995-1997. More information [here](http://frotz.sourceforge.net/).

Download this source code, then perform the following commands.

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
$ frotz/dfrotz games/zork1.z5
```

## Games

Games are provided in this repo, but more games are available [here](http://www.ifarchive.org/indexes/if-archiveXgamesXzcode.html).

## Miscellaneous

If you are the copyright holder for any of these game files and object to their distribution in this repository, e-mail the owner at daniel.ricks4 (-a-t-) gmail.com.
