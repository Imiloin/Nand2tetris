# VMTranslator.py

import os
import sys
from Parser import Parser
from CodeWriter import CodeWriter


class VMTranslator:
    def __init__(self, input_path):
        self.input_path = input_path
        self.parser = None
        if os.path.isdir(input_path):
            self.output_file_name = os.path.basename(input_path)
            self.output_file = open(os.path.join(self.input_path, self.output_file_name + '.asm'), 'w')
        else:
            self.output_file_name = os.path.splitext(os.path.basename(input_path))[0]
            self.output_file = open(os.path.splitext(self.input_path)[0] + '.asm', 'w')
        self.code_writer = CodeWriter(input_path)

    def translate(self):
        # 输入是目录
        if os.path.isdir(self.input_path):
            # 如果存在 Sys.vm 文件，则写入 bootstrap code
            sys_file_path = os.path.join(self.input_path, 'Sys.vm')
            if os.path.isfile(sys_file_path):
                self.code_writer.write_init()
                need_end_loop = False
            else:
                need_end_loop = True
            # 遍历目录下的所有 .vm 文件
            for file_name in os.listdir(self.input_path):
                if file_name.endswith('.vm'):
                    self.translate_file(os.path.join(self.input_path, file_name))
        # 输入是 vm 文件
        else:
            self.translate_file(self.input_path)
            need_end_loop = True
        if need_end_loop:
            self.code_writer.write('(END_LOOP)')
            self.code_writer.write('@END_LOOP')
            self.code_writer.write('0;JMP')
        self.code_writer.close()

    # 翻译单个 .vm 文件
    def translate_file(self, vmfile_path):
        self.parser = Parser(vmfile_path)
        self.code_writer.set_file_name(os.path.basename(vmfile_path))
        while self.parser.has_more_commands():
            self.parser.advance()
            # 如果是空行或注释行，则跳过
            if not self.parser.current_command:
                continue
            # 写入注释表示该行原本的 VM 代码
            self.code_writer.write_comment(self.parser.current_command)
            # 解析命令类型并调用 CodeWriter 的相应方法
            command_type = self.parser.command_type()
            if command_type == 'C_ARITHMETIC':
                self.code_writer.write_arithmetic(self.parser.arg1())
            elif command_type in ['C_PUSH', 'C_POP']:
                self.code_writer.write_push_pop(command_type, self.parser.arg1(), self.parser.arg2())
            elif command_type == 'C_LABEL':
                self.code_writer.write_label(self.parser.arg1())
            elif command_type == 'C_GOTO':
                self.code_writer.write_goto(self.parser.arg1())
            elif command_type == 'C_IF':
                self.code_writer.write_if(self.parser.arg1())
            elif command_type == 'C_FUNCTION':
                self.code_writer.write_function(self.parser.arg1(), self.parser.arg2())
            elif command_type == 'C_RETURN':
                self.code_writer.write_return()
            elif command_type == 'C_CALL':
                self.code_writer.write_call(self.parser.arg1(), self.parser.arg2())


# 运行 VMTranslator.py 入口
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python VMTranslator.py <file_name.vm or input_directory>')
    else:
        input_path = sys.argv[1]
        if not os.path.exists(input_path):
            print(f'Error: {input_path} does not exist')
        elif os.path.isfile(input_path) and not input_path.endswith('.vm'):
            print(f'Error: {input_path} is not a .vm file')
        else:
            vm_translator = VMTranslator(input_path)
            vm_translator.translate()
