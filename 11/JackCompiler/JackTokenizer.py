KEYWORDS = {"class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void",
            "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"}
SYMBOLS = {"{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"}
# SYMBOLS_MAP = {"<": "&lt;", ">": "&gt;", '"': "&quot;", "&": "&amp;"}


class JackTokenizer:
    def __init__(self, input_file):
        # 读取输入文件
        with open(input_file, "r") as f:
            self.lines = f.readlines()

        # 初始化指针和当前标记
        self.pointer = 0  # 指向当前行
        self.in_comment = False  # 是否在注释中
        self.current_token = None
        self.token_type = None
        self.line = self.lines[self.pointer].strip()
        self.file_name = input_file

    def has_more_tokens(self):
        # 判断是否还有更多标记，删除无效行和注释
        # 仅当还有未处理的行时，才有更多标记
        while True:
            while self.line:
                if "//" in self.line:
                    self.line = self.line[:self.line.index("//")].strip()
                elif "/*" in self.line:
                    start_index = self.line.index("/*")
                    if "*/" in self.line[start_index + 2:]:
                        end_index = self.line.index("*/", start_index + 2)
                        self.line = self.line[:start_index] + self.line[end_index + 2:]
                    else:
                        self.in_comment = True
                        break
                elif self.in_comment:
                    if "*/" in self.line:
                        end_index = self.line.index("*/")
                        self.line = self.line[end_index + 2:]
                        self.in_comment = False
                    else:
                        break
                else:
                    return True
            self.pointer += 1
            if self.pointer >= len(self.lines):
                return False
            self.line = self.lines[self.pointer].strip()

    def advance(self):
        # 获取下一个标记，获取后直接从lines中删除
        # 此时没有无效行和注释，仅有token
        if self.in_comment:
            raise ValueError(f"File {self.file_name}, in line {self.currentLine()}, unexpected end of file: missing */")
        elif self.line.startswith('"'):
            # 处理字符串常量
            end_index = self.line.index('"', 1)
            self.current_token = self.line[1:end_index]
            self.token_type = "stringConstant"
            self.line = self.line[end_index + 1:].strip()
        elif self.line[0].isdigit():
            # 处理数字常量
            end_index = 0
            while end_index < len(self.line) and self.line[end_index] not in SYMBOLS and self.line[end_index] != " ":
                end_index += 1
            self.current_token = self.line[:end_index]
            self.token_type = "integerConstant"
            if not self.current_token.isdigit():
                raise ValueError(f"File {self.file_name}, in line {self.currentLine()}, invalid variable name '{self.current_token}' (starts with number)")
            elif int(self.current_token) > 32767:
                raise ValueError(f"File {self.file_name}, in line {self.currentLine()}, integer constant '{self.current_token}' out of range")
            self.line = self.line[end_index:].strip()
        elif self.line[0] in SYMBOLS:
            # 处理符号
            self.current_token = self.line[0]
            # if self.current_token in SYMBOLS_MAP:
            #     self.current_token = SYMBOLS_MAP[self.current_token]
            self.token_type = "symbol"
            self.line = self.line[1:].strip()
        else:
            # 处理关键字和标识符
            end_index = 0
            while end_index < len(self.line) and self.line[end_index] not in SYMBOLS and self.line[end_index] != " ":
                end_index += 1
            self.current_token = self.line[:end_index]
            if self.current_token in KEYWORDS:
                self.token_type = "keyword"
            else:
                self.token_type = "identifier"
            self.line = self.line[end_index:].strip()

    def tokenType(self):
        # 获取当前标记的类型
        return self.token_type
    
    def token(self):
        # 获取当前标记
        return self.current_token

    def keyword(self):
        # 获取当前关键字
        if self.token_type != "keyword":
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.currentLine()}, invalid keyword '{self.current_token}'")
        return self.current_token

    def symbol(self):
        # 获取当前符号
        if self.token_type != "symbol":
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.currentLine()}, invalid symbol '{self.current_token}'")
        return self.current_token

    def identifier(self):
        # 获取当前标识符
        if self.token_type != "identifier":
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.currentLine()}, invalid identifier '{self.current_token}'")
        return self.current_token

    def intVal(self):
        # 获取当前整数
        if self.token_type != "integerConstant":
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.currentLine()}, invalid integer constant '{self.current_token}'")
        return int(self.current_token)

    def stringVal(self):
        # 获取当前字符串
        if self.token_type != "stringConstant":
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.currentLine()}, invalid string constant '{self.current_token}'")
        return self.current_token
    
    def currentLine(self):
        # 获取当前行数
        return self.pointer + 1
