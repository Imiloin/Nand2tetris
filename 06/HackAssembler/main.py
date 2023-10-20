import os
import re


def variable_num():
    n = 16
    while n < 16384:
        yield n
        n += 1
    return 'done'


num = variable_num()


def translate_A_instruction(instruction):
    if instruction.startswith('@'):
        value = instruction[1:]
        if value.isdigit():
            binary_code = '0' + bin(int(value))[2:].zfill(15)
        elif value in label_dict:
            binary_code = '0' + bin(label_dict[value])[2:].zfill(15)
        else:
            label_dict[value] = next(num)
            binary_code = '0' + bin(label_dict[value])[2:].zfill(15)
            # print(value)
            # print(label_dict[value])
            # print(binary_code)
        return binary_code
    else:
        raise SyntaxError('Invalid A-instruction')


def translate_C_instruction(instruction):
    dest = ''
    comp = ''
    jump = ''
    if '=' in instruction:
        dest, comp = instruction.split('=')
    if ';' in instruction:
        comp, jump = instruction.split(';')
    return '111' + code_dict[comp] + dest_dict[dest] + jump_dict[jump]


code_dict = {
    '0': '0101010',
    '1': '0111111',
    '-1': '0111010',
    'D': '0001100',
    'A': '0110000',
    '!D': '0001101',
    '!A': '0110001',
    '-D': '0001111',
    '-A': '0110011',
    'D+1': '0011111',
    'A+1': '0110111',
    'D-1': '0001110',
    'A-1': '0110010',
    'D+A': '0000010',
    'D-A': '0010011',
    'A-D': '0000111',
    'D&A': '0000000',
    'D|A': '0010101',
    'M': '1110000',
    '!M': '1110001',
    '-M': '1110011',
    'M+1': '1110111',
    'M-1': '1110010',
    'D+M': '1000010',
    'D-M': '1010011',
    'M-D': '1000111',
    'D&M': '1000000',
    'D|M': '1010101',
}

dest_dict = {
    '': '000',
    'M': '001',
    'D': '010',
    'MD': '011',
    'A': '100',
    'AM': '101',
    'AD': '110',
    'AMD': '111',
}

jump_dict = {
    '': '000',
    'JGT': '001',
    'JEQ': '010',
    'JGE': '011',
    'JLT': '100',
    'JNE': '101',
    'JLE': '110',
    'JMP': '111',
}

filename = input('Please input the file name:')
filepath, ext = os.path.splitext(filename)
filename = os.path.basename(filepath).split('.')[0]
if not ext:
    ext = '.asm'


with open(filename + ext, 'r') as f:
    code = f.read()

# 删除注释
code = re.sub(r'//.*', '', code)
code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

# 删除空行和多余的空格
code = '\n'.join(line.strip() for line in code.split('\n') if line.strip())

# print(code)

label_dict = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7, 'R8': 8, 'R9': 9, 'R10': 10,
              'R11': 11, 'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15, 'SCREEN': 16384, 'KBD': 24576,
              'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4}
lines = code.split('\n')
line_num = 0

for line in lines:
    line = line.strip()

    # 如果这一行是标签，则记录下标签对应的行数
    if line.startswith('('):
        if line.endswith(')'):
            label = line[1:-1]
            label_dict[label] = line_num
        else:
            raise SyntaxError('Missing right parenthesis')
    else:
        line_num += 1

# 删除代码中的标签
code = re.sub(r'\([^)]*\)\n', '', code)

# print(code)
# print(label_dict)


lines = code.split('\n')

with open(filename + '.hack', "w") as f:
    for line in lines:
        line = line.strip()

        # 如果这一行是标签，则记录下标签对应的行数
        if line.startswith('@'):
            t = translate_A_instruction(line)
            f.write(t + '\n')
        else:
            t = translate_C_instruction(line)
            f.write(t + '\n')

    f.seek(0, 2)  # 移动文件指针到文件末尾
    f.seek(f.tell() - 2)  # 移动文件指针到倒数第二个字符
    f.truncate()  # 删除倒数第二个字符（即最后的换行符）
