import os
import sys
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


def process_file(file_path):
    # 生成输出文件名
    if os.path.splitext(file_path)[1] != ".jack":
        print(f"Invalid input file {file_path}")
        return
    ## output_file = os.path.splitext(file_path)[0] + ".xml"
    ## token_output_file = os.path.splitext(file_path)[0] + "T.xml"
    # for test, add a 0 to the end of the output file name
    output_file = os.path.splitext(file_path)[0] + "0.xml"
    token_output_file = os.path.splitext(file_path)[0] + "T0.xml"

    # 初始化 JackTokenizer 和 CompilationEngine
    tokenizer = JackTokenizer(file_path)
    engine = CompilationEngine(tokenizer, file_path, token_output_file, output_file)

    # 开始编译
    engine.compile()


def process_directory(directory_path):
    # 处理目录中的所有 .jack 文件
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".jack"):
            file_path = os.path.join(directory_path, file_name)
            process_file(file_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python JackAnalyzer.py <file_name.jack or input_directory>")
    else:
        # 获取输入参数
        input_path = sys.argv[1]
        # 判断输入参数是文件还是目录
        if not os.path.exists(input_path):
            print(f'Error: {input_path} does not exist')
        elif os.path.isfile(input_path):
            process_file(input_path)
        elif os.path.isdir(input_path):
            process_directory(input_path)
        else:
            print("Invalid input path")
            print("Usage: python JackAnalyzer.py <file_name.jack or input_directory>")
