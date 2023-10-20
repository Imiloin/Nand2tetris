import os
import sys
from CompilationEngine import CompilationEngine


class JackCompiler:
    def __init__(self, input_path):
        self.input_path = input_path
        self.engine = CompilationEngine(input_path)

    def compile(self):
        self.engine.compile()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file_name.jack or input_directory>")
    else:
        # 获取输入参数
        input_path = sys.argv[1]
        if not os.path.exists(input_path):
            print(f'Error: {input_path} does not exist')
            print("Usage: python JackCompiler.py <file_name.jack or input_directory>")
        elif os.path.isfile(input_path) and not input_path.endswith('.jack'):
            print(f'Error: {input_path} is not a .jack file')
            print("Usage: python JackCompiler.py <file_name.jack or input_directory>")
        else:
            jack_compiler = JackCompiler(input_path)
            jack_compiler.compile()
