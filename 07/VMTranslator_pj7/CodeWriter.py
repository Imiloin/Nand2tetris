# CodeWriter.py

import os


class CodeWriter:
    def __init__(self, output_file):
        self.output_file = output_file
        self.file = open(output_file, 'w')
        self.current_function = None
        self.label_index = 0

    def write_arithmetic(self, command):
        if command == 'add':
            self.write_binary_op('+')
        elif command == 'sub':
            self.write_binary_op('-')
        elif command == 'neg':
            self.write_unary_op('-')
        elif command == 'eq':
            self.write_comparison('JEQ')
        elif command == 'gt':
            self.write_comparison('JGT')
        elif command == 'lt':
            self.write_comparison('JLT')
        elif command == 'and':
            self.write_binary_op('&')
        elif command == 'or':
            self.write_binary_op('|')
        elif command == 'not':
            self.write_unary_op('!')

    def write_push_pop(self, command_type, segment, index):
        if command_type == 'C_PUSH':
            if segment == 'constant':
                self.write_push_constant(index)
            elif segment in ['local', 'argument', 'this', 'that']:
                self.write_push_segment(segment, index)
            elif segment == 'temp':
                self.write_push_temp(index)
            elif segment == 'pointer':
                self.write_push_pointer(index)
            elif segment == 'static':
                self.write_push_static(index)
        elif command_type == 'C_POP':
            if segment in ['local', 'argument', 'this', 'that']:
                self.write_pop_segment(segment, index)
            elif segment == 'temp':
                self.write_pop_temp(index)
            elif segment == 'pointer':
                self.write_pop_pointer(index)
            elif segment == 'static':
                self.write_pop_static(index)

    def write_push_constant(self, index):
        self.write_comment(f'push constant {index}')
        self.write('@' + str(index))
        self.write('D=A')
        self.write_push_D()

    def write_push_segment(self, segment, index):
        self.write_comment(f'push {segment} {index}')
        self.write('@' + str(index))
        self.write('D=A')
        self.write('@' + self.get_segment_base(segment))
        self.write('A=D+M')
        self.write('D=M')
        self.write_push_D()

    def write_push_temp(self, index):
        self.write_comment(f'push temp {index}')
        self.write('@' + str(5 + index))
        self.write('D=M')
        self.write_push_D()

    def write_push_pointer(self, index):
        self.write_comment(f'push pointer {index}')
        self.write('@' + str(3 + index))
        self.write('D=M')
        self.write_push_D()

    def write_push_static(self, index):
        self.write_comment(f'push static {index}')
        self.write('@' + os.path.splitext(self.output_file)[0] + '.' + str(index))
        self.write('D=M')
        self.write_push_D()

    def write_pop_segment(self, segment, index):
        self.write_comment(f'pop {segment} {index}')
        self.write('@' + str(index))
        self.write('D=A')
        self.write('@' + self.get_segment_base(segment))
        self.write('D=D+M')
        self.write('@R13')
        self.write('M=D')
        self.write_pop_D()
        self.write('@R13')
        self.write('A=M')
        self.write('M=D')

    def write_pop_temp(self, index):
        self.write_comment(f'pop temp {index}')
        self.write_pop_D()
        self.write('@' + str(5 + index))
        self.write('M=D')

    def write_pop_pointer(self, index):
        self.write_comment(f'pop pointer {index}')
        self.write_pop_D()
        self.write('@' + str(3 + index))
        self.write('M=D')

    def write_pop_static(self, index):
        self.write_comment(f'pop static {index}')
        self.write_pop_D()
        self.write('@' + os.path.splitext(self.output_file)[0] + '.' + str(index))
        self.write('M=D')

    def write_binary_op(self, op):
        self.write_comment(f'{op}')
        self.write_pop_D()
        self.write('@SP')
        self.write('A=M-1')
        self.write(f'M=M{op}D')

    def write_unary_op(self, op):
        self.write_comment(f'{op}')
        self.write('@SP')
        self.write('A=M-1')
        self.write(f'M={op}M')

    def write_comparison(self, jump):
        self.write_comment(f'{jump}')
        self.write_pop_D()
        self.write('@SP')
        self.write('A=M-1')
        self.write('D=M-D')
        self.write('@TRUE' + str(self.label_index))
        self.write(f'D;{jump}')
        self.write('@SP')
        self.write('A=M-1')
        self.write('M=0')
        self.write('@FALSE' + str(self.label_index))
        self.write('0;JMP')
        self.write('(TRUE' + str(self.label_index) + ')')
        self.write('@SP')
        self.write('A=M-1')
        self.write('M=-1')
        self.write('(FALSE' + str(self.label_index) + ')')
        self.label_index += 1

    def write_push_D(self):
        self.write('@SP')
        self.write('A=M')
        self.write('M=D')
        self.write('@SP')
        self.write('M=M+1')

    def write_pop_D(self):
        self.write('@SP')
        self.write('M=M-1')
        self.write('A=M')
        self.write('D=M')

    def get_segment_base(self, segment):
        if segment == 'local':
            return 'LCL'
        elif segment == 'argument':
            return 'ARG'
        elif segment == 'this':
            return 'THIS'
        elif segment == 'that':
            return 'THAT'

    def write_comment(self, comment):
        self.write(f'// {comment}')

    def write(self, code):
        self.file.write(code + '\n')

    def close(self):
        self.file.close()