# VMTranslator.py

import os
import sys
from Parser import Parser
from CodeWriter import CodeWriter


class VMTranslator:
    def __init__(self, input_file):
        self.input_file = input_file
        self.parser = Parser(input_file)
        self.code_writer = CodeWriter(os.path.splitext(input_file)[0] + '.asm')

    def translate(self):
        while self.parser.has_more_commands():
            self.parser.advance()
            command_type = self.parser.command_type()
            if command_type == 'C_ARITHMETIC':
                self.code_writer.write_arithmetic(self.parser.arg1())
            elif command_type in ['C_PUSH', 'C_POP']:
                self.code_writer.write_push_pop(command_type, self.parser.arg1(), self.parser.arg2())
            # add more command types here if needed
        self.code_writer.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python VMTranslator.py <input_file.vm>')
    else:
        input_file = sys.argv[1]
        if not os.path.isfile(input_file):
            print(f'Error: {input_file} does not exist')
        elif not input_file.endswith('.vm'):
            print(f'Error: {input_file} is not a .vm file')
        else:
            vm_translator = VMTranslator(input_file)
            vm_translator.translate()
