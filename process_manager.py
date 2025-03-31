import os
import signal
from signal import signal, SIGPIPE, SIG_DFL
from subprocess import PIPE, Popen
from threading import Thread
from queue import Queue, Empty

class ProcessManager:
    def __init__(self, game_filename):
        signal(SIGPIPE, SIG_DFL)
        self.game_loaded_properly = True

        # Verify that specified game file exists, else limit functionality
        if game_filename == None or not os.path.exists('games/' + game_filename):
            self.game_loaded_properly = False
            print("Unrecognized game file or bad path")
            return

        self.game_filename = game_filename
        self.game_log = game_filename + '_log.txt'
        self.debug = False

    def start_game(self):
        if self.game_loaded_properly == True:
            # Start the game process with both 'standard in' and 'standard out' pipes
            self.game_process = Popen(['./frotz/dfrotz', 'games/' + self.game_filename], stdin=PIPE, stdout=PIPE)

            # Create Queue object
            self.output_queue = Queue()
            t = Thread(target=self.enqueue_pipe_output, args=(self.game_process.stdout, self.output_queue))

            # Thread dies with the program
            t.daemon = True
            t.start()

            return True
        return False

    def enqueue_pipe_output(self, output, queue):
        for line in iter(output.readline, b''):
            queue.put(line.decode('utf-8', errors='ignore'))
        output.close()

    def send_command(self, command):
        if self.game_loaded_properly == True:
            self.game_process.stdin.write((command + '\n').encode())
            self.game_process.stdin.flush()
            return True
        return False

    def get_raw_output(self):
        command_output = ''
        output_continues = True

        # While there is still output in the queue
        while (output_continues):
            try:
                line = self.output_queue.get(timeout=.001)
            except Empty:
                output_continues = False
            else:
                command_output += line

        return command_output

    def quit(self):
        if self.game_loaded_properly == True:
            self.game_process.stdin.write(b'quit\n')
            self.game_process.stdin.flush()
            self.game_process.stdin.write(b'y\n')
            self.game_process.stdin.flush()
        if self.game_process.stdin != None:
            self.game_process.stdin.write(b'n\n')
            self.game_process.stdin.flush()
