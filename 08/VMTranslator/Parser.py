# Parser.py

from enum import Enum


class Parser:
    def __init__(self, input_file):
        self.input_file = input_file
        with open(input_file, 'r') as f:
            self.lines = f.readlines()
        self.current_command = None
        self.current_index = -1
        self.current_command_type = None

    def has_more_commands(self):
        return self.current_index < len(self.lines) - 1

    def advance(self):
        self.current_index += 1
        self.current_command = self.lines[self.current_index].strip()
        # 去除注释
        if '//' in self.current_command:
            self.current_command = self.current_command[:self.current_command.index('//')].strip()

    def command_type(self):
        if not self.current_command:
            return None
        words = self.current_command.split()
        if len(words) == 1:
            if words[0] in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
                self.current_command_type = 'C_ARITHMETIC'
            elif words[0] == 'return':
                self.current_command_type = 'C_RETURN'
            else:
                self.current_command_type = None
        elif len(words) == 2:
            if words[0] == 'label':
                self.current_command_type = 'C_LABEL'
            elif words[0] == 'goto':
                self.current_command_type = 'C_GOTO'
            elif words[0] == 'if-goto':
                self.current_command_type = 'C_IF'
            else:
                self.current_command_type = None
        elif len(words) == 3:
            if words[0] == 'push':
                self.current_command_type = 'C_PUSH'
            elif words[0] == 'pop':
                self.current_command_type = 'C_POP'
            elif words[0] == 'function':
                self.current_command_type = 'C_FUNCTION'
            elif words[0] == 'call':
                self.current_command_type = 'C_CALL'
            else:
                self.current_command_type = None
        else:
            self.current_command_type = None
        return self.current_command_type

    def arg1(self):
        # 如果是算术命令，则返回算术命令本身（如 add、sub 等）
        if self.command_type() == 'C_ARITHMETIC':
            return self.current_command
        # 否则返回第一个参数
        else:
            return self.current_command.split()[1]

    def arg2(self):
        return int(self.current_command.split()[2])
