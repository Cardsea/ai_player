import os, sys, signal, time, re
from signal import signal, SIGPIPE, SIG_DFL
from subprocess import PIPE, Popen
from threading import Thread
from queue import Queue, Empty
from text_manager import TextManager

'''
 Currently, for games that require several clicks to get start info, it doesn't scrape everything. Lost.z5 is one. The first couple commands will not produce the expected output.

 Class Summary: TextPlayer([name of the game file])
 Methods:	run()
 			parse_and_execute_command_file([text file containing a list of commands])
 			execute_command([command string])
			get_score(), returns None if no score found, returns ('2', '100') if 2/100 found
			quit()
'''

class TextPlayer:

	# Initializes the class, sets variables
	def __init__(self, game_filename):
		signal(SIGPIPE, SIG_DFL)
		self.text_manager = TextManager(game_filename)
		self.game_loaded_properly = self.text_manager.game_loaded_properly

		# Verify that specified game file exists, else limit functionality
		if game_filename == None or not os.path.exists('games/' + game_filename):
			self.game_loaded_properly = False
			print("Unrecognized game file or bad path")
			return

		self.game_filename = game_filename
		self.game_log = game_filename + '_log.txt'
		self.debug = False

	# Runs the game
	def run(self):
		if self.game_loaded_properly == True:
			return self.text_manager.run()

	# Parses through a text list of commands (or a single command) and executes them
	def parse_and_execute_command_file(self, input_filename):
		if self.game_loaded_properly == True:
			self.text_manager.parse_and_execute_command_file(input_filename)

	# Send a command to the game and return the output
	def execute_command(self, command):
		if self.game_loaded_properly == True:
			return self.text_manager.execute_command(command)

	# Returns the current score in a game
	def get_score(self):
		if self.game_loaded_properly == True:
			return self.text_manager.get_score()
		return None

	def quit(self):
		if self.game_loaded_properly == True:
			self.text_manager.quit()
