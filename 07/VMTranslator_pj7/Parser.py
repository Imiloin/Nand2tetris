# Parser.py

class Parser:
    def __init__(self, input_file):
        self.input_file = input_file
        with open(input_file, 'r') as f:
            self.lines = f.readlines()
        self.current_command = None
        self.current_index = -1

    def has_more_commands(self):
        return self.current_index < len(self.lines) - 1

    def advance(self):
        self.current_index += 1
        self.current_command = self.lines[self.current_index].strip()
        if '//' in self.current_command:
            self.current_command = self.current_command[:self.current_command.index('//')].strip()

    def command_type(self):
        if self.current_command.startswith('push'):
            return 'C_PUSH'
        elif self.current_command.startswith('pop'):
            return 'C_POP'
        elif self.current_command in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
            return 'C_ARITHMETIC'
        # add more command types here if needed

    def arg1(self):
        if self.command_type() == 'C_ARITHMETIC':
            return self.current_command
        else:
            return self.current_command.split()[1]

    def arg2(self):
        return int(self.current_command.split()[2])
