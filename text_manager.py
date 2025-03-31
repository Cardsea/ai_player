import re
from process_manager import ProcessManager

class TextManager:
    def __init__(self, game_filename):
        self.process_manager = ProcessManager(game_filename)
        self.game_loaded_properly = self.process_manager.game_loaded_properly

    def run(self):
        if self.game_loaded_properly:
            if self.process_manager.start_game():
                # Grab start info from game
                start_output = self.get_command_output()
                if 'Press' in start_output or 'press' in start_output or 'Hit' in start_output or 'hit' in start_output:
                    start_output += self.execute_command(' \n')
                if 'introduction' in start_output:
                    start_output += self.execute_command('no\n')  # Parc
                return start_output
        return None

    def parse_and_execute_command_file(self, input_filename):
        if self.game_loaded_properly:
            if (os.path.exists(input_filename)):
                with open(input_filename, 'r') as f:
                    commands = f.read()
                    if '\n' in commands:
                        for command in commands.split('\n'):
                            print(self.execute_command(command))
                    else:
                        print(self.execute_command(commands))

    def execute_command(self, command):
        if self.game_loaded_properly:
            self.process_manager.send_command(command)
            return self.clean_command_output(self.get_command_output())

    def get_score(self):
        if self.game_loaded_properly:
            self.process_manager.send_command('score')
            command_output = self.get_command_output()
            score_pattern = r'[0-9]+ [(]total [points ]*[out ]*of [a maximum of ]*[a possible ]*[0-9]+'
            matchObj = re.search(score_pattern, command_output, re.M|re.I)
            if matchObj != None:
                score_words = matchObj.group().split(' ')
                return int(score_words[0]), int(score_words[len(score_words)-1])
        return None

    def clean_command_output(self, text):
        regex_list = ['[0-9]+/[0-9+]', 'Score:[ ]*[-]*[0-9]+', 'Moves:[ ]*[0-9]+',
                     'Turns:[ ]*[0-9]+', '[0-9]+:[0-9]+ [AaPp][Mm]', r' [0-9]+ \.']
        for regex in regex_list:
            matchObj = re.search(regex, text, re.M|re.I)
            if matchObj != None:
                text = text[matchObj.end() + 1:]
        return text

    def get_command_output(self):
        command_output = self.process_manager.get_raw_output()
        # Clean up the output but preserve newlines
        command_output = command_output.replace('\n\n', '\n').replace('>', ' ').replace('<', ' ')
        # Only replace multiple spaces with a single space, but preserve newlines
        while '  ' in command_output:
            command_output = command_output.replace('  ', ' ')
        return command_output

    def quit(self):
        if self.game_loaded_properly:
            self.process_manager.quit()
