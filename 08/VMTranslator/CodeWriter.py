# CodeWriter.py

import os


class CodeWriter:
    def __init__(self, input_path):
        # 输入是目录，将目录名作为输出 asm 文件名
        if os.path.isdir(input_path):
            self.output_file_name = os.path.basename(input_path)
            self.file = open(os.path.join(input_path, self.output_file_name + '.asm'), 'w')
        # 输入是 vm 文件，将输入文件名作为输出 asm 文件名
        else:
            self.output_file_name = os.path.splitext(os.path.basename(input_path))[0]
            self.file = open(os.path.splitext(input_path)[0] + '.asm', 'w')
        self.current_function = None
        self.current_file_name = None
        self.label_index = 0

    # 写入 bootstrap code
    def write_init(self):
        self.write('// bootstrap code')
        self.write('@256')
        self.write('D=A')
        self.write('@SP')
        self.write('M=D')
        self.write_call('Sys.init', 0)

    # 设置当前文件名
    def set_file_name(self, file_name):
        self.current_file_name = os.path.splitext(file_name)[0]
        self.write_comment('file name: ' + file_name)

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
        self.write('@' + str(index))
        self.write('D=A')
        self.write_push_D()

    def write_push_segment(self, segment, index):
        self.write('@' + str(index))
        self.write('D=A')
        self.write('@' + self.get_segment_base(segment))
        self.write('A=D+M')
        self.write('D=M')
        self.write_push_D()

    def write_push_temp(self, index):
        self.write('@' + str(5 + index))
        self.write('D=M')
        self.write_push_D()

    def write_push_pointer(self, index):
        self.write('@' + str(3 + index))
        self.write('D=M')
        self.write_push_D()

    def write_push_static(self, index):
        self.write('@' + self.current_file_name + '.' + str(index))
        self.write('D=M')
        self.write_push_D()

    def write_pop_segment(self, segment, index):
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
        self.write_pop_D()
        self.write('@' + str(5 + index))
        self.write('M=D')

    def write_pop_pointer(self, index):
        self.write_pop_D()
        self.write('@' + str(3 + index))
        self.write('M=D')

    def write_pop_static(self, index):
        self.write_pop_D()
        self.write('@' + self.current_file_name + '.' + str(index))
        self.write('M=D')

    def write_binary_op(self, op):
        self.write_pop_D()
        self.write('@SP')
        self.write('A=M-1')
        self.write(f'M=M{op}D')

    def write_unary_op(self, op):
        self.write('@SP')
        self.write('A=M-1')
        self.write(f'M={op}M')

    def write_comparison(self, jump):
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

    def write_label(self, label):
        self.write(f'({self.current_function_name()}${label})')

    def write_goto(self, label):
        self.write('@' + self.current_function_name() + '$' + label)
        self.write('0;JMP')

    def write_if(self, label):
        self.write_pop_D()
        self.write('@' + self.current_function_name() + '$' + label)
        self.write('D;JNE')

    def write_function(self, function_name, num_locals):
        self.current_function = function_name
        self.write('(' + function_name + ')')
        for i in range(int(num_locals)):
            self.write_push_pop('C_PUSH', 'constant', '0')

    def write_call(self, function_name, num_args):
        return_label = f'{function_name}${self.label_index}'
        self.label_index += 1

        # push return-address
        self.write(f'@{return_label}')
        self.write(f'D=A')
        self.write(f'@SP')
        self.write(f'M=M+1')
        self.write(f'A=M-1')
        self.write(f'M=D')

        # push LCL
        self.write(f'@LCL')
        self.write(f'D=M')
        self.write(f'@SP')
        self.write(f'M=M+1')
        self.write(f'A=M-1')
        self.write(f'M=D')

        # push ARG
        self.write(f'@ARG')
        self.write(f'D=M')
        self.write(f'@SP')
        self.write(f'M=M+1')
        self.write(f'A=M-1')
        self.write(f'M=D')

        # push THIS
        self.write(f'@THIS')
        self.write(f'D=M')
        self.write(f'@SP')
        self.write(f'M=M+1')
        self.write(f'A=M-1')
        self.write(f'M=D')

        # push THAT
        self.write(f'@THAT')
        self.write(f'D=M')
        self.write(f'@SP')
        self.write(f'M=M+1')
        self.write(f'A=M-1')
        self.write(f'M=D')

        # ARG = SP - n - 5
        self.write(f'@SP')
        self.write(f'D=M')
        self.write(f'@{num_args}')
        self.write(f'D=D-A')
        self.write(f'@5')
        self.write(f'D=D-A')
        self.write(f'@ARG')
        self.write(f'M=D')

        # LCL = SP
        self.write(f'@SP')
        self.write(f'D=M')
        self.write(f'@LCL')
        self.write(f'M=D')

        # goto function_name
        self.write(f'@{function_name}')
        self.write(f'0;JMP')

        # (return-address)
        self.write(f'({return_label})')

    def write_return(self):
        # FRAME = LCL
        self.write('@LCL')
        self.write('D=M')
        self.write('@R13')
        self.write('M=D')

        # RET = *(FRAME-5)
        self.write('@5')
        self.write('A=D-A')
        self.write('D=M')
        self.write('@R14')
        self.write('M=D')

        # *ARG = pop()
        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")

        # SP = ARG + 1
        self.write('@ARG')
        self.write('D=M+1')
        self.write('@SP')
        self.write('M=D')

        # THAT = *(FRAME-1)
        self.write('@R13')
        self.write('AM=M-1')
        self.write('D=M')
        self.write('@THAT')
        self.write('M=D')

        # THIS = *(FRAME-2)
        self.write('@R13')
        self.write('AM=M-1')
        self.write('D=M')
        self.write('@THIS')
        self.write('M=D')

        # ARG = *(FRAME-3)
        self.write('@R13')
        self.write('AM=M-1')
        self.write('D=M')
        self.write('@ARG')
        self.write('M=D')

        # LCL = *(FRAME-4)
        self.write('@R13')
        self.write('A=M-1')
        self.write('D=M')
        self.write('@LCL')
        self.write('M=D')

        # goto RET
        self.write('@R14')
        self.write('A=M')
        self.write('0;JMP')

    def current_function_name(self):
        if self.current_function:
            return self.current_function
        else:
            return self.current_file_name

    def write_comment(self, comment):
        self.write(f'// {comment}')

    def write(self, code):
        self.file.write(code + '\n')

    def close(self):
        self.file.close()
