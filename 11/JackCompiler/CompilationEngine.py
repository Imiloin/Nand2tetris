import os
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter


BUILD_IN_CLASSES = {"Array", "Keyboard", "Math", "Memory", "Output", "Screen", "String", "Sys"}
# 内置类局部变量数不会写入 vm 文件，因此设置为 -1
BUILD_IN_SUBROUTINES = {"Array": ([-1, -1], {"new": ["constructor", False, 1, -1], "dispose": ["method", True, 1, -1]}),
                        "Keyboard": ([-1, -1], {"keyPressed": ["function", False, 0, -1], "readChar": ["function", False, 0, -1], "readLine": ["function", False, 1, -1], "readInt": ["function", False, 1, -1]}),
                        "Math": ([-1, -1], {"abs": ["function", False, 1, -1], "multiply": ["function", False, 2, -1], "divide": ["function", False, 2, -1], "min": ["function", False, 2, -1], "max": ["function", False, 2, -1], "sqrt": ["function", False, 1, -1]}),
                        "Memory": ([-1, -1], {"peek": ["function", False, 1, -1], "poke": ["function", True, 2, -1], "alloc": ["function", False, 1, -1], "deAlloc": ["function", True, 1, -1]}),
                        "Output": ([-1, -1], {"moveCursor": ["function", True, 2, -1], "printChar": ["function", True, 1, -1], "printString": ["function", True, 1, -1], "printInt": ["function", True, 1, -1], "println": ["function", True, 0, -1], "backSpace": ["function", True, 0, -1]}),
                        "Screen": ([-1, -1], {"clearScreen": ["function", True, 0, -1], "setColor": ["function", True, 1, -1], "drawPixel": ["function", True, 2, -1], "drawLine": ["function", True, 4, -1], "drawRectangle": ["function", True, 4, -1], "drawCircle": ["function", True, 3, -1]}),
                        "String": ([-1, -1], {"new": ["constructor", False, 1, -1], "dispose": ["method", True, 1, -1], "length": ["method", False, 1, -1], "charAt": ["method", False, 2, -1], "setCharAt": ["method", True, 3, -1], "appendChar": ["method", False, 2, -1], "eraseLastChar": ["method", True, 1, -1], "intValue": ["method", False, 1, -1], "setInt": ["method", True, 2, -1], "backSpace": ["function", False, 0, -1], "doubleQuote": ["function", False, 0, -1], "newLine": ["function", False, 0, -1]}),
                        "Sys": ([-1, -1], {"halt": ["function", True, 0, -1], "error": ["function", True, 1, -1], "wait": ["function", True, 1, -1]}), }


class CompilationEngine:
    def __init__(self, input_path):
        self.input_path = input_path
        self.tokenizer = None
        self.writer = None
        self.current_statement = ""  # 当前语句
        self.file_name = ""  # 当前jack文件的名字
        self.file_name_only = ""  # 当前jack文件的名字，不含后缀
        self.output_file = ""  # 当前输出vm文件的名字
        self.class_name = ""  # 当前类的名字
        self.class_table = SymbolTable()  # 当前类的符号表
        self.have_constructor = False  # 当前类是否有constructor
        self.subroutine_name = ""  # 当前subroutine的名字
        self.subroutine_type = ""  # 当前subroutine的类别，'constructor'|'function'|'method'
        self.subroutine_table = SymbolTable()  # 当前subroutine的符号表
        self.have_return = False  # 当前subroutine是否有return语句
        self.subroutine_is_void = False  # 当前subroutine是否是void类型
        self.undefined_build_in_classes = BUILD_IN_CLASSES  # 未自行定义的内置类
        self.defined_classes = {}  # 已经定义过的类型，类型名为key，value为 ([定义处的文件名, 行数], {定义的子程序0: [子程序类别，是否为void，参数个数，局部变量数], 定义的子程序2: [子程序类别，是否为void，参数个数，局部变量数], ...})
        self.if_count = 0  # if语句的数量
        self.while_count = 0  # while语句的数量
    
    def compile(self):
        # 先扫描，再编译
        # 扫描时，检查语法，生成类表
        if os.path.isfile(self.input_path):
            self.scan_file(self.input_path)
            self.compile_file(self.input_path)
        elif os.path.isdir(self.input_path):
            for file_name in os.listdir(self.input_path):
                if file_name.endswith(".jack"):
                    file_path = os.path.join(self.input_path, file_name)
                    self.file_name_only = os.path.splitext(file_name)[0]
                    self.scan_file(file_path)
            # 增加未自行定义的内置类支持
            for class_name in self.undefined_build_in_classes:
                self.defined_classes[class_name] = BUILD_IN_SUBROUTINES[class_name]
            for file_name in os.listdir(self.input_path):
                if file_name.endswith(".jack"):
                    file_path = os.path.join(self.input_path, file_name)
                    self.compile_file(file_path)

    def scan_file(self, file_path):
        self.file_name = file_path
        if self.file_name_only in self.undefined_build_in_classes:
            self.undefined_build_in_classes.remove(self.file_name_only)
        # 初始化 JackTokenizer
        self.tokenizer = JackTokenizer(file_path)
        # 开始扫描
        while self.tokenizer.has_more_tokens():
            self.scan_class()

    def scan_class(self):  # at last
        # class: 'class' className '{' classVarDec* subroutineDec* '}'
        self.class_table = SymbolTable()  # 当前类的符号表
        self.have_constructor = False  # 当前类是否有constructor
        self.current_statement = f"line {self.tokenizer.currentLine()}: "
        # 'class'
        self.advance("keyword", "class")
        self.scan_keyword("class")
        # className
        self.class_name = self.advance("identifier")
        if self.class_name != self.file_name_only:
            print(f"(Warning) File {self.file_name}, in line {self.tokenizer.currentLine()}, class name '{self.class_name}' is different from file name '{self.file_name_only}'")
        self.scan_identifier()
        if self.class_name in self.defined_classes:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, class '{self.class_name}' has already been defined in file {self.defined_classes[self.class_name][0][0]} line {self.defined_classes[self.class_name][0][1]}")
        self.defined_classes[self.class_name] = ([self.file_name, self.tokenizer.currentLine()], {})
        # '{'
        self.advance("symbol", "{")
        self.scan_symbol("{")
        self.try_advance("Unfinished class")
        # classVarDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["static", "field"]:
            self.scan_class_var_dec()
            self.try_advance("Expected a '}' in class")
        # subroutineDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["constructor", "function", "method"]:
            self.scan_subroutine()
            self.try_advance("Expected a '}' in class")
        # '}'
        self.scan_symbol("}")
        # check if the class has a constructor
        if self.have_constructor is False and self.class_name != "Main":
            print(f"(Warning) File {self.file_name}, in line {self.tokenizer.currentLine()}, class '{self.class_name}' has no constructor")

    def scan_class_var_dec(self):  # at last
        # classVarDec: ('static'|'field') type varName (',' varName)* ';'
        # ('static'|'field')
        kind = self.tokenizer.keyword()
        self.scan_keyword(kind)
        self.try_advance("Expected a type in classVarDec")
        # type
        type_ = self.scan_type()
        # varName
        name = self.advance("identifier")
        self.scan_identifier()
        self.class_var_define(name, type_, kind)
        self.try_advance("Expected a ';' in classVarDec")
        # (',' varName)*
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.scan_symbol(",")
            name = self.advance("identifier")
            self.scan_identifier()
            self.class_var_define(name, type_, kind)
            self.try_advance("Expected a ';' in classVarDec")
        # ;

    def scan_subroutine(self):  # at last
        # subroutineDec: ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody
        self.subroutine_table = SymbolTable()  # 当前subroutine的符号表
        self.have_return = False
        self.subroutine_is_void = False
        # ('constructor'|'function'|'method')
        self.subroutine_type = self.tokenizer.keyword()
        self.scan_keyword(self.subroutine_type)
        if self.tokenizer.keyword() == "method":
            self.subroutine_var_define("this", self.class_name, "argument")
        elif self.tokenizer.keyword() == "constructor":
            if self.have_constructor:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, class '{self.class_name}' has more than one constructor")
            self.have_constructor = True
        # raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has wrong type '{self.tokenizer.keyword()}'")
        self.try_advance("Expected a type in subroutineDec")
        # ('void'|type)
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "void":
            self.scan_keyword(self.tokenizer.keyword())
            self.subroutine_is_void = True
        else:
            type_ = self.scan_type()
            # check if the constructor has the same name as the class
            if self.subroutine_type == "constructor" and type_ != self.class_name:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, constructor has wrong return type '{type_}', expected '{self.class_name}'")
        self.advance("identifier")
        self.scan_identifier()
        # subroutineName
        self.subroutine_name = self.tokenizer.identifier()
        self.init_subroutine()
        # check if the constructor has the expected name 'new'
        if self.subroutine_type == "constructor" and self.subroutine_name != "new":
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, constructor has wrong name '{self.subroutine_name}', expected 'new'")
        # (
        self.advance("symbol", "(")
        self.scan_symbol("(")
        # parameterList
        self.try_advance("Expected a parameter list in subroutineDec")
        self.scan_parameter_list()
        # )
        self.scan_symbol(")")
        self.scan_subroutine_body()
        if self.have_return is False:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has no return statement")

    def scan_parameter_list(self):  # at next
        # parameterList: ((type varName) (',' type varName)*)?
        if self.subroutine_type == "method":
            n_args = 1
        else:
            n_args = 0
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            type_ = self.scan_type()
            name = self.advance("identifier")
            self.scan_identifier()
            self.subroutine_var_define(name, type_, "argument")
            n_args += 1
            self.try_advance("Unfinished parameterList")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.scan_symbol(",")
                self.try_advance("Unfinished parameterList")
        self.set_subroutine_n_args(n_args)
    
    def scan_subroutine_body(self):  # at last
        # subroutineBody: '{' varDec* statements '}'
        # {
        self.advance("symbol", "{")
        self.scan_symbol("{")
        self.try_advance("Unfinished subroutineBody")
        # varDec*
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "var":
            n_locals = 0
            while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "var":
                n_locals += self.scan_var_dec()
                self.try_advance("Unfinished subroutineBody")
            self.set_subroutine_n_locals(n_locals)
        else:  # no varDec
            self.set_subroutine_n_locals(0)
        # # if self.subroutine_type == "constructor":
        # # elif self.subroutine_type == "method":
        # statements
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != "}":
            self.scan_statements()
        # }
        self.scan_symbol("}")

    def scan_var_dec(self):  # at last, return n_vars
        # varDec: 'var' type varName (',' varName)* ';'
        n_vars = 0
        # var
        self.scan_keyword("var")
        self.try_advance("Expected a type in varDec")
        # type
        type_ = self.scan_type()
        # varName
        name = self.advance("identifier")
        self.scan_identifier()
        self.subroutine_var_define(name, type_, "local")
        n_vars += 1
        self.try_advance("Expected a ';' in varDec")
        # (',' varName)*
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.scan_symbol(",")
            name = self.advance("identifier")
            self.scan_identifier()
            self.subroutine_var_define(name, type_, "local")
            n_vars += 1
            self.try_advance("Expected a ';' in varDec")
        # ;
        self.scan_symbol(";")
        return n_vars
    
    def scan_statements(self):  # at next
        # statements: statement*
        while self.tokenizer.tokenType() == "keyword":
            keyword = self.tokenizer.keyword()
            if keyword == "let":
                self.scan_let()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "if":
                self.scan_if()
            elif keyword == "while":
                self.scan_while()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "do":
                self.scan_do()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "return":
                self.scan_return()
                self.try_advance("Expected a '}' in statements")
                break  # return语句后面不应该再有语句
            else:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid keyword '{keyword}'")

    def scan_let(self):  # at last
        # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
        self.scan_keyword("let")
        self.advance("identifier")
        self.scan_identifier()
        self.try_advance("Expected a '=' in letStatement")
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
            self.scan_symbol("[")
            self.try_advance("Expected an expression in '[]'")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "]":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected an expression in '[]'")
            self.scan_expression()
            self.scan_symbol("]")
            self.advance("symbol", "=")
        self.scan_symbol("=")
        self.try_advance("Expected an expression right of '=' in letStatement")
        self.scan_expression()
        self.scan_symbol(";")

    def scan_if(self):  # at next
        # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        self.scan_keyword("if")
        self.advance("symbol", "(")
        self.scan_symbol("(")
        self.try_advance("Expected an expression in '()'")
        self.scan_expression()
        self.scan_symbol(")")
        self.advance("symbol", "{")
        self.scan_symbol("{")
        self.try_advance("Expected a '}'")
        self.scan_statements()
        self.scan_symbol("}")
        self.try_advance("Expected a '}' in Statements")
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "else":
            self.scan_keyword("else")
            self.advance("symbol", "{")
            self.scan_symbol("{")
            self.try_advance("Expected a '}'")
            self.scan_statements()
            self.scan_symbol("}")
            self.try_advance("Expected a '}' in Statements")

    def scan_while(self):  # at last
        # whileStatement: 'while' '(' expression ')' '{' statements '}'
        self.scan_keyword("while")
        self.advance("symbol", "(")
        self.scan_symbol("(")
        self.try_advance("Expected an expression in '()'")
        self.scan_expression()
        self.scan_symbol(")")
        self.advance("symbol", "{")
        self.scan_symbol("{")
        self.try_advance("Expected a '}'")
        self.scan_statements()
        self.scan_symbol("}")

    def scan_do(self):  # at last
        # doStatement: 'do' subroutineCall ';'
        self.scan_keyword("do")
        name = self.advance("identifier")
        self.scan_identifier()
        self.try_advance("Expected a subroutineCall")
        self.scan_subroutine_call(name)
        self.advance("symbol", ";")
        self.scan_symbol(";")

    def scan_return(self):  # at last
        # returnStatement: 'return' expression? ';'
        self.scan_keyword("return")
        self.try_advance("Expected an expression or ';' in returnStatement")
        if self.subroutine_is_void:
            if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ";":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, void function '{self.subroutine_name}' should not return a value")
        elif self.subroutine_type == "constructor":
            if self.tokenizer.tokenType() != "keyword" or self.tokenizer.keyword() != "this":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, constructor '{self.subroutine_name}' should return 'this' instead of '{self.tokenizer.token()}'")
            self.scan_expression()
        else:
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ";":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, function '{self.subroutine_name}' should return a value")    
            self.scan_expression()
        self.scan_symbol(";")
        # 一个subroutine可以在分支中含有多个return语句
        self.have_return = True

    def scan_expression(self):  # at next
        # expression: term (op term)*
        self.scan_term()
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            self.scan_symbol(self.tokenizer.symbol())
            self.tokenizer.advance()
            self.scan_term()

    def scan_term(self):  # at next
        # term: integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        token_type = self.tokenizer.tokenType()
        if token_type == "integerConstant":
            # integerConstant
            self.scan_integer()
            self.try_advance("Expected a ';'")
        elif token_type == "stringConstant":
            # stringConstant
            self.scan_string()
            # # string = self.tokenizer.stringVal()
            self.try_advance("Expected a ';'")
        elif token_type == "keyword" and self.tokenizer.keyword() in ["true", "false", "null", "this"]:
            # keywordConstant
            keyword = self.tokenizer.keyword()
            self.scan_keyword(keyword)
            self.try_advance("Expected a ';'")
        elif token_type == "identifier":
            self.scan_identifier()
            name = self.tokenizer.identifier()  # varName | subroutineName | className
            self.try_advance("Unfinished term")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
                # varName[expression]
                ###
                self.scan_symbol("[")
                self.try_advance("Expected an expression in '[]'")
                self.scan_expression()
                self.scan_symbol("]")
                self.try_advance("Expected a ';'")
            elif self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["(", "."]:
                # subroutineCall
                self.scan_subroutine_call(name)
                self.try_advance("Expected a ';'")
            else:
                # varName
                pass
        elif token_type == "symbol" and self.tokenizer.symbol() == "(":
            # (expression)
            self.scan_symbol("(")
            self.try_advance("Expected a ')'")
            self.scan_expression()
            self.scan_symbol(")")
            self.try_advance("Expected a ';'")
        elif token_type == "symbol" and self.tokenizer.symbol() in ["-", "~"]:
            # unaryOp term
            op = self.tokenizer.symbol()
            self.scan_symbol(op)
            self.try_advance(f"Unfinished term {self.tokenizer.token()}")
            self.scan_term()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid term '{self.tokenizer.token()}'")

    def scan_subroutine_call(self, name):  # at last
        # subroutineName(expressionList) | (className|varName).subroutineName'('expressionList')'
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ".":
            self.scan_symbol(".")
            self.advance("identifier")
            self.scan_identifier()
            self.advance("symbol")
        self.scan_symbol("(")
        self.try_advance("Expected an expressionList in '()'")
        self.scan_expression_list()
        self.scan_symbol(")")

    def scan_expression_list(self):  # at next
        # expressionList: (expression (',' expression)*)?
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            self.scan_expression()
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.scan_symbol(",")
                self.try_advance("Unfinished expressionList after ','")

    def scan_type(self):  # at last, return type
        # _type: 'int'|'char'|'boolean'|className
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["int", "char", "boolean"]:
            return self.tokenizer.keyword()
        elif self.tokenizer.tokenType() == "identifier":
            self.scan_identifier()
            return self.tokenizer.identifier()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid type '{self.tokenizer.token()}'")

    def init_subroutine(self):
        if self.subroutine_name in self.defined_classes[self.class_name][1]:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has already been defined in class '{self.class_name}'")
        self.defined_classes[self.class_name][1][self.subroutine_name] = [self.subroutine_type, self.subroutine_is_void, -1, -1]
    
    def set_subroutine_n_args(self, n_args):
        if self.defined_classes[self.class_name][1][self.subroutine_name][2] == -1:
            self.defined_classes[self.class_name][1][self.subroutine_name][2] = n_args
        else:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' n_args has already been set")

    def set_subroutine_n_locals(self, n_locals):
        if self.defined_classes[self.class_name][1][self.subroutine_name][3] == -1:
            self.defined_classes[self.class_name][1][self.subroutine_name][3] = n_locals
        else:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' n_locals has already been set")
    
    def scan_keyword(self, keyword):
        if self.tokenizer.tokenType() != "keyword" or self.tokenizer.keyword() != keyword:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a '{keyword}', but got '{self.tokenizer.token()}'")

    def scan_symbol(self, symbol):
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != symbol:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a '{symbol}', but got '{self.tokenizer.token()}'")

    def scan_identifier(self):
        if self.tokenizer.tokenType() != "identifier":
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected an identifier, but got '{self.tokenizer.token()}'")

    def scan_integer(self):
        if self.tokenizer.tokenType() != "integerConstant":
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected an integerConstant, but got '{self.tokenizer.token()}'")

    def scan_string(self):
        if self.tokenizer.tokenType() != "stringConstant":
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a stringConstant, but got '{self.tokenizer.token()}'")

    def compile_file(self, file_path):
        self.file_name = file_path
        self.output_file = os.path.splitext(file_path)[0] + ".vm"
        # 初始化 JackTokenizer 和 VMWriter
        self.tokenizer = JackTokenizer(file_path)
        self.writer = VMWriter(self.output_file)
        # 开始编译
        self.writer.open()
        while self.tokenizer.has_more_tokens():
            self.compile_class()
        self.writer.close()

    def compile_class(self):  # at last
        # class: 'class' className '{' classVarDec* subroutineDec* '}'
        self.class_table = SymbolTable()  # 当前类的符号表
        self.have_constructor = False  # 当前类是否有constructor
        self.current_statement = f"line {self.tokenizer.currentLine()}: "
        # 'class'
        self.advance("keyword", "class")
        self.comment_keyword("class")
        # className
        self.class_name = self.advance("identifier")
        self.comment_identifier()
        # '{'
        self.advance("symbol", "{")
        self.comment_symbol("{")
        self.write_comment()
        self.try_advance("Unfinished class")
        # classVarDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["static", "field"]:
            self.compile_class_var_dec()
            self.try_advance("Expected a '}' in class")
        # subroutineDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["constructor", "function", "method"]:
            self.compile_subroutine()
            self.try_advance("Expected a '}' in class")
        # '}'
        self.comment_symbol("}")

    def compile_class_var_dec(self):  # at last
        # classVarDec: ('static'|'field') type varName (',' varName)* ';'
        # ('static'|'field')
        kind = self.tokenizer.keyword()
        self.comment_keyword(kind)
        self.try_advance("Expected a type in classVarDec")
        # type
        type_ = self.compile_type()
        # varName
        name = self.advance("identifier")
        self.comment_identifier()
        self.class_var_define(name, type_, kind)
        self.try_advance("Expected a ';' in classVarDec")
        # (',' varName)*
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.comment_symbol(",")
            name = self.advance("identifier")
            self.comment_identifier()
            self.class_var_define(name, type_, kind)
            self.try_advance("Expected a ';' in classVarDec")
        # ;
        self.write_comment()

    def compile_subroutine(self):  # at last
        # subroutineDec: ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody
        self.subroutine_table = SymbolTable()  # 当前subroutine的符号表
        self.have_return = False
        self.subroutine_is_void = False
        # ('constructor'|'function'|'method')
        self.subroutine_type = self.tokenizer.keyword()
        self.comment_keyword(self.subroutine_type)
        if self.tokenizer.keyword() == "method":
            self.subroutine_var_define("this", self.class_name, "argument")
        elif self.tokenizer.keyword() == "constructor":
            if self.have_constructor:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, class '{self.class_name}' has more than one constructor")
            self.have_constructor = True
        # raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has wrong type '{self.tokenizer.keyword()}'")
        self.try_advance("Expected a type in subroutineDec")
        # ('void'|type)
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "void":
            self.comment_keyword(self.tokenizer.keyword())
            self.subroutine_is_void = True
        else:
            type_ = self.compile_type()
            # check if the constructor has the same name as the class
            if self.subroutine_type == "constructor" and type_ != self.class_name:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, constructor has wrong return type '{type_}', expected '{self.class_name}'")
        self.advance("identifier")
        self.comment_identifier()
        # subroutineName
        self.subroutine_name = self.tokenizer.identifier()
        # check if the constructor has the expected name 'new'
        if self.subroutine_type == "constructor" and self.subroutine_name != "new":
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, constructor has wrong name '{self.subroutine_name}', expected 'new'")
        self.write_comment()
        # (
        self.advance("symbol", "(")
        self.comment_symbol("(")
        # parameterList
        self.try_advance("Expected a parameter list in subroutineDec")
        self.compile_parameter_list()
        # )
        self.comment_symbol(")")
        # # self.write_comment()
        self.compile_subroutine_body()
        if self.have_return is False:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has no return statement")

    def compile_parameter_list(self):  # at next
        # parameterList: ((type varName) (',' type varName)*)?
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            type_ = self.compile_type()
            name = self.advance("identifier")
            self.comment_identifier()
            self.subroutine_var_define(name, type_, "argument")
            self.try_advance("Unfinished parameterList")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.comment_symbol(",")
                self.try_advance("Unfinished parameterList")
    
    def compile_subroutine_body(self):  # at last
        # subroutineBody: '{' varDec* statements '}'
        # {
        self.advance("symbol", "{")
        self.comment_symbol("{")
        self.write_comment()
        self.try_advance("Unfinished subroutineBody")
        # varDec*
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "var":
            self.compile_var_dec()
            self.try_advance("Unfinished subroutineBody")
        self.writer.write_function(f"{self.class_name}.{self.subroutine_name}", self.subroutine_table.var_count("local"))
        if self.subroutine_type == "constructor":
            self.writer.write_push("constant", self.class_table.var_count("field"))
            self.writer.write_call("Memory.alloc", 1)
            self.writer.write_pop("pointer", 0)
        elif self.subroutine_type == "method":
            self.writer.write_push("argument", 0)
            self.writer.write_pop("pointer", 0)
        # statements
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != "}":
            self.compile_statements()
        # }
        self.comment_symbol("}")

    def compile_var_dec(self):  # at last
        # varDec: 'var' type varName (',' varName)* ';'
        # var
        self.comment_keyword("var")
        self.try_advance("Expected a type in varDec")
        # type
        type_ = self.compile_type()
        # varName
        name = self.advance("identifier")
        self.comment_identifier()
        self.subroutine_var_define(name, type_, "local")
        self.try_advance("Expected a ';' in varDec")
        # (',' varName)*
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.comment_symbol(",")
            name = self.advance("identifier")
            self.comment_identifier()
            self.subroutine_var_define(name, type_, "local")
            self.try_advance("Expected a ';' in varDec")
        # ;
        self.comment_symbol(";")
        self.write_comment()
    
    def compile_statements(self):  # at next
        # statements: statement*
        while self.tokenizer.tokenType() == "keyword":
            keyword = self.tokenizer.keyword()
            if keyword == "let":
                self.compile_let()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "if":
                self.compile_if()
            elif keyword == "while":
                self.compile_while()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "do":
                self.compile_do()
                self.try_advance("Expected a '}' in statements")
            elif keyword == "return":
                self.compile_return()
                self.try_advance("Expected a '}' in statements")
                self.write_comment()
                break  # return语句后面不应该再有语句
            else:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid keyword '{keyword}'")

    def compile_let(self):  # at last
        # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
        # let
        self.comment_keyword("let")
        name = self.advance("identifier")
        # varName
        self.comment_identifier()
        var_type, var_kind, var_index = self.search_var(name)
        if var_type == "Array":
            construct_array = True
        else:
            construct_array = False
        # # print(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, {var_type}, {var_kind}, {var_index}")
        self.try_advance("Expected a '=' in letStatement")
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
            # varName[expression]
            self.writer.write_push(var_kind, var_index)
            construct_array = False
            # [
            if var_type != "Array":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, variable '{name}' is not an array")
            self.comment_symbol("[")
            self.try_advance("Expected an expression in '[]'")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "]":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected an expression in '[]'")
            # expression
            self.compile_expression()
            self.writer.write_arithmetic("add")
            # ]
            self.comment_symbol("]")
            self.advance("symbol", "=")
        # =
        self.comment_symbol("=")
        self.try_advance("Expected an expression right of '=' in letStatement")
        # expression
        self.compile_expression()
        # ;
        if var_type == "Array" and not construct_array:
            self.writer.write_pop("temp", 0)
            self.writer.write_pop("pointer", 1)
            self.writer.write_push("temp", 0)
            self.writer.write_pop("that", 0)
        else:
            self.writer.write_pop(var_kind, var_index)
        self.comment_symbol(";")
        self.write_comment()

    def compile_if(self):  # at next
        # build in version #
        # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if_index = self.if_count
        self.if_count += 1
        # if
        self.comment_keyword("if")
        self.advance("symbol", "(")
        # (
        self.comment_symbol("(")
        self.try_advance("Expected an expression in '()'")
        # expression
        self.compile_expression()
        self.writer.write_if(f"IF_TRUE{if_index}")  # if-goto L1
        self.writer.write_goto(f"IF_FALSE{if_index}")  # goto L2
        # )
        self.comment_symbol(")")
        self.writer.write_label(f"IF_TRUE{if_index}")  # label L1
        self.advance("symbol", "{")
        # {
        self.comment_symbol("{")
        self.write_comment()
        self.try_advance("Expected a '}'")
        # statements
        self.compile_statements()
        # }
        self.comment_symbol("}")
        self.write_comment()
        self.try_advance("Expected a '}' in Statements")
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "else":
            # else
            self.comment_keyword("else")
            self.writer.write_goto(f"IF_END{if_index}")  # goto END
            self.writer.write_label(f"IF_FALSE{if_index}")  # label L2
            self.advance("symbol", "{")
            # {
            self.comment_symbol("{")
            self.write_comment()
            self.try_advance("Expected a '}'")
            # statements
            self.compile_statements()
            # }
            self.comment_symbol("}")
            self.writer.write_label(f"IF_END{if_index}")  # label END
            self.write_comment()
            self.try_advance("Expected a '}' in Statements")
        else:
            # 无 else 语句
            self.writer.write_label(f"IF_FALSE{if_index}")  # label L2
    
    def _compile_if(self):  # at next
        # my version #
        # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if_index = self.if_count
        self.if_count += 1
        # if
        self.comment_keyword("if")
        self.advance("symbol", "(")
        # (
        self.comment_symbol("(")
        self.try_advance("Expected an expression in '()'")
        # expression
        self.compile_expression()
        self.writer.write_arithmetic("not")  # not
        self.writer.write_if(f"IF_TRUE{if_index}")  # if-goto L1
        # )
        self.comment_symbol(")")
        self.advance("symbol", "{")
        # {
        self.comment_symbol("{")
        self.write_comment()
        self.try_advance("Expected a '}'")
        # statements
        self.compile_statements()
        # }
        self.comment_symbol("}")
        self.write_comment()
        self.try_advance("Expected a '}' in Statements")
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "else":
            # else
            self.comment_keyword("else")
            self.writer.write_goto(f"IF_FALSE{if_index}")  # goto L2
            self.writer.write_label(f"IF_TRUE{if_index}")  # label L1
            self.advance("symbol", "{")
            # {
            self.comment_symbol("{")
            self.write_comment()
            self.try_advance("Expected a '}'")
            # statements
            self.compile_statements()
            self.writer.write_label(f"IF_FALSE{if_index}")  # label L2
            # }
            self.comment_symbol("}")
            self.write_comment()
            self.try_advance("Expected a '}' in Statements")
        else:
            # 无 else 语句
            self.writer.write_label(f"IF_TRUE{if_index}")  # label L1

    def compile_while(self):  # at last
        # whileStatement: 'while' '(' expression ')' '{' statements '}'
        while_index = self.while_count
        self.while_count += 1
        # while
        self.comment_keyword("while")
        self.writer.write_label(f"WHILE_EXP{while_index}")  # label L1
        self.advance("symbol", "(")
        # (
        self.comment_symbol("(")
        self.try_advance("Expected an expression in '()'")
        # expression
        self.compile_expression()
        self.writer.write_arithmetic("not")  # not
        # )
        self.comment_symbol(")")
        self.writer.write_if(f"WHILE_END{while_index}")  # if-goto L2
        self.advance("symbol", "{")
        # {
        self.comment_symbol("{")
        self.try_advance("Expected a '}'")
        # statements
        self.compile_statements()
        self.writer.write_goto(f"WHILE_EXP{while_index}")  # goto L1
        # }
        self.comment_symbol("}")
        self.writer.write_label(f"WHILE_END{while_index}")  # label L2
        self.write_comment()

    def compile_do(self):  # at last
        # doStatement: 'do' subroutineCall ';'
        # do
        self.comment_keyword("do")
        # subroutineCall
        name = self.advance("identifier")
        self.comment_identifier()
        self.try_advance("Expected a subroutineCall")
        self.compile_subroutine_call(name)
        self.advance("symbol", ";")
        # ;
        self.comment_symbol(";")
        self.write_comment()

    def compile_return(self):  # at last
        # returnStatement: 'return' expression? ';'
        # return
        self.comment_keyword("return")
        self.try_advance("Expected an expression in returnStatement")
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ";":
            self.writer.write_push("constant", 0)
        else:
            # expression
            self.compile_expression()
        # ;
        self.comment_symbol(";")
        self.writer.write_return()
        self.have_return = True
        # # self.write_comment()

    def compile_expression(self):  # at next
        # expression: term (op term)*
        # push expression
        self.compile_term()
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            op = self.tokenizer.symbol()  # 二元运算符
            self.comment_symbol(op)
            self.try_advance(f"Missing a term after {op}")
            self.compile_term()
            if op == "+":
                self.writer.write_arithmetic("add")
            elif op == "-":
                self.writer.write_arithmetic("sub")
            elif op == "*":
                self.writer.write_call("Math.multiply", 2)
            elif op == "/":
                self.writer.write_call("Math.divide", 2)
            elif op == "&":
                self.writer.write_arithmetic("and")
            elif op == "|":
                self.writer.write_arithmetic("or")
            elif op == "<":
                self.writer.write_arithmetic("lt")
            elif op == ">":
                self.writer.write_arithmetic("gt")
            elif op == "=":
                # '=' 相当于 '=='
                self.writer.write_arithmetic("eq")
            else:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid op '{op}'")

    def compile_term(self):  # at next
        # term: integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        # push term
        token_type = self.tokenizer.tokenType()
        if token_type == "integerConstant":
            # integerConstant
            self.comment_integer()
            self.writer.write_push("constant", self.tokenizer.intVal())
            self.try_advance("Expected a ';'")
        elif token_type == "stringConstant":
            # stringConstant
            self.comment_string()
            string = self.tokenizer.stringVal()
            self.writer.write_push("constant", len(string))
            self.writer.write_call("String.new", 1)
            for char in string:
                self.writer.write_push("constant", ord(char))
                self.writer.write_call("String.appendChar", 2)
            self.try_advance("Expected a ';'")
        elif token_type == "keyword" and self.tokenizer.keyword() in ["true", "false", "null", "this"]:
            # keywordConstant
            keyword = self.tokenizer.keyword()
            self.comment_keyword(keyword)
            if keyword == "true":
                self.writer.write_push("constant", 0)
                self.writer.write_arithmetic("not")
            elif keyword in ["false", "null"]:
                self.writer.write_push("constant", 0)
            elif keyword == "this":
                self.writer.write_push("pointer", 0)
            else:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid keyword '{keyword}'")
            self.try_advance("Expected a ';'")
        elif token_type == "identifier":
            name = self.tokenizer.identifier()  # varName | subroutineName | className
            self.comment_identifier()
            self.try_advance("Unfinished term")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
                # varName[expression]
                self.push_var(name)
                self.comment_symbol("[")
                self.try_advance("Expected an expression in '[]'")
                self.compile_expression()
                self.comment_symbol("]")
                self.writer.write_arithmetic("add")
                self.writer.write_pop("pointer", 1)
                self.writer.write_push("that", 0)
                self.try_advance("Expected a ';'")
            elif self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["(", "."]:
                # subroutineCall
                self.compile_subroutine_call(name)
                self.try_advance("Expected a ';'")
            else:
                # varName
                self.push_var(name)
        elif token_type == "symbol" and self.tokenizer.symbol() == "(":
            # (expression)
            self.comment_symbol("(")
            self.try_advance("Expected a ')'")
            self.compile_expression()
            self.comment_symbol(")")
            self.try_advance("Expected a ';'")
        elif token_type == "symbol" and self.tokenizer.symbol() in ["-", "~"]:
            # unaryOp term
            op = self.tokenizer.symbol()
            self.comment_symbol(op)
            self.try_advance(f"Unfinished term {self.tokenizer.token()}")
            self.compile_term()
            if op == "-":
                self.writer.write_arithmetic("neg")
            elif op == "~":
                self.writer.write_arithmetic("not")
            else:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid unaryOp '{op}'")
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid term '{self.tokenizer.token()}'")

    def compile_subroutine_call(self, name):  # at last
        # subroutineName(expressionList) | (className|varName).subroutineName'('expressionList')'
        # subroutineName已经写入注释
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ".":
            # (className|varName).subroutineName(expressionList)
            # '.'
            self.comment_symbol(".")
            if name in self.defined_classes:
                # definedClassName.subroutineName'('expressionList')'
                callee_class = name
                # subroutineName
                callee_name = self.advance("identifier")
                n_args = self.get_subroutine_n_args(name, callee_name)
                self.comment_identifier()
                self.advance("symbol")
                # '('
                self.comment_symbol("(")
                self.try_advance("Expected an expressionList in '()'")
                if self.get_subroutine_type(name, callee_name) in ["constructor", "function"]:
                    # definedClassName.(function|constructor)'('expressionList')'
                    n_args_in_expression_list = self.compile_expression_list()
                elif self.get_subroutine_type(name, callee_name) == "method":
                    # definedClassName.method'('expressionList')'
                    n_args_in_expression_list = self.compile_expression_list(callee_class)
                else:
                    raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine type '{self.get_subroutine_type(name, callee_name)}'")
                if n_args_in_expression_list != n_args:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, '{callee_name}' needs {n_args} arguments, but got {n_args_in_expression_list}")
                # ')'
                self.comment_symbol(")")
            else:
                # varName.method'('expressionList')'
                # push varName
                callee_class, var_kind, var_index = self.push_var(name)
                callee_name = self.advance("identifier")
                # subroutineName
                self.comment_identifier()
                if self.get_subroutine_type(callee_class, callee_name) != "method":
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, '{callee_name}' is a '{self.get_subroutine_type}', not a method")
                n_args = self.get_subroutine_n_args(callee_class, callee_name)
                self.advance("symbol")
                # '('
                self.comment_symbol("(")
                self.try_advance("Expected an expressionList in '()'")
                n_args_in_expression_list = self.compile_expression_list()
                if n_args_in_expression_list + 1 != n_args:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, method '{callee_name}' needs {n_args} arguments, but got {n_args_in_expression_list + 1}")
                # ')'
                self.comment_symbol(")")
        elif self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "(":
            # methodOrFunctionInCurrentClass'('expressionList')'
            callee_class = self.class_name
            callee_name = name
            callee_type = self.get_subroutine_type(self.class_name, name)
            if callee_type == "method":
                if self.subroutine_type not in ["constructor", "method"]:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, subroutine '{self.subroutine_name}' is a '{self.subroutine_type}', not a method or constructor, but try to call '{callee_type}' '{name}'")
                self.writer.write_push("pointer", 0)
                n_args = self.get_subroutine_n_args(self.class_name, name)
                # '('
                self.comment_symbol("(")
                self.try_advance("Expected an expressionList in '()'")
                n_args_in_expression_list = self.compile_expression_list()
                if n_args_in_expression_list + 1 != n_args:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, method '{callee_name}' needs {n_args} arguments, but got {n_args_in_expression_list + 1}")
                # ')'
                self.comment_symbol(")")
            elif callee_type == "function":
                n_args = self.get_subroutine_n_args(self.class_name, name)
                # '('
                self.comment_symbol("(")
                self.try_advance("Expected an expressionList in '()'")
                n_args_in_expression_list = self.compile_expression_list()
                if n_args_in_expression_list != n_args:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, function '{callee_name}' needs {n_args} arguments, but got {n_args_in_expression_list}")
                # ')'
                self.comment_symbol(")")
            elif callee_type == "constructor":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call, '{name}' is a constructor, should be called with {self.class_name}.{name}()")
            else:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine type '{callee_type}' of '{name}'")
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid subroutine call '{self.tokenizer.token()}'")
        self.writer.write_call(f"{callee_class}.{callee_name}", n_args)
        if self.get_subroutine_is_void(callee_class, callee_name):
            self.writer.write_pop("temp", 0)

    def compile_expression_list(self, expected_first_arg_class=None):  # at next, return n_args in expressionList
        # expressionList: (expression (',' expression)*)?
        n_args_in_expression_list = 0
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            if expected_first_arg_class is not None:
                first_arg = self.tokenizer.identifier()
                var_type, var_kind, var_index = self.search_var(first_arg)
                if var_type != expected_first_arg_class:
                    raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid method call, expected first argument of type '{expected_first_arg_class}', but got '{var_type}'")
            else:
                self.compile_expression()
            n_args_in_expression_list += 1
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.comment_symbol(",")
                self.try_advance("Unfinished expressionList after ','")
        return n_args_in_expression_list

    def compile_type(self):  # at last, return type
        # _type: 'int'|'char'|'boolean'|className
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["int", "char", "boolean"]:
            return self.tokenizer.keyword()
        elif self.tokenizer.tokenType() == "identifier":
            self.comment_identifier()
            return self.tokenizer.identifier()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid type '{self.tokenizer.token()}'")
    
    def class_var_define(self, name, type_, kind):
        if not self.class_table.define(name, type_, kind):
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, duplicate class variable '{name}'")
    
    def subroutine_var_define(self, name, type_, kind):
        if self.class_table.in_table(name):
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine variable '{name}' has the same name as a class variable")
        elif not self.subroutine_table.define(name, type_, kind):
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, duplicate subroutine variable '{name}'")
    
    def push_var(self, name):  # return var_type, var_kind, var_index
        # search in subroutine table
        if self.subroutine_table.kind_of(name) is not None:
            var_type = self.subroutine_table.type_of(name)
            var_kind = self.subroutine_table.kind_of(name)
            var_index = self.subroutine_table.index_of(name)
            self.writer.write_push(var_kind, var_index)
            return var_type, var_kind, var_index
        # search in class table
        elif self.class_table.kind_of(name) is not None:
            var_type = self.class_table.type_of(name)
            var_kind = self.class_table.kind_of(name)
            var_index = self.class_table.index_of(name)
            if var_kind == "field":
                self.writer.write_push("this", var_index)
                var_kind = "this"
            elif var_kind == "static":
                self.writer.write_push("static", var_index)
            else:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid kind '{self.class_table.kind_of(name)}'")
            return var_type, var_kind, var_index
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined variable '{name}'")

    def search_var(self, name):  # do not push, return var_type, var_kind, var_index
        # search in subroutine table
        if self.subroutine_table.kind_of(name) is not None:
            var_type = self.subroutine_table.type_of(name)
            var_kind = self.subroutine_table.kind_of(name)
            var_index = self.subroutine_table.index_of(name)
            return var_type, var_kind, var_index
        # search in class table
        elif self.class_table.kind_of(name) is not None:
            var_type = self.class_table.type_of(name)
            var_kind = self.class_table.kind_of(name)
            var_index = self.class_table.index_of(name)
            if var_kind not in ["field", "static"]:
                raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid kind '{self.class_table.kind_of(name)}'")
            if var_kind == "field":
                var_kind = "this"
            return var_type, var_kind, var_index
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined variable '{name}'")
    
    def advance(self, expected_token_type, expected_token=None):
        # 前进一个token，如果不是期望的token，抛出异常，返回当前token
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            if self.tokenizer.tokenType() != expected_token_type:
                line_num = self.tokenizer.currentLine()
                if expected_token is None:
                    raise ValueError(f"File {self.file_name}, in line {line_num}, expected a {expected_token_type}, but got '{self.tokenizer.token()}'")
                else:
                    raise ValueError(f"File {self.file_name}, in line {line_num}, expected {expected_token_type} '{expected_token}', but got '{self.tokenizer.token()}'")
            elif expected_token is not None and self.tokenizer.token() != expected_token:
                line_num = self.tokenizer.currentLine()
                raise ValueError(f"File {self.file_name}, in line {line_num}, expected {expected_token_type} '{expected_token}', but got '{self.tokenizer.token()}'")
            return self.tokenizer.token()
        else:
            line_num = self.tokenizer.currentLine()
            if expected_token is None:
                raise ValueError(f"File {self.file_name}, in line {line_num}, expected a {expected_token_type}, but no more tokens")
            else:
                raise ValueError(f"File {self.file_name}, in line {line_num}, expected {expected_token_type} '{expected_token}', but no more tokens")

    def try_advance(self, error_msg):
        # 前进一个token，如果没有更多token，抛出异常
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, {error_msg}, but no more tokens")

    def just_advance(self):
        # 前进一个token，不做任何检查
        self.tokenizer.advance()
    
    def get_subroutine_type(self, class_name, subroutine_name):
        if subroutine_name not in self.defined_classes[class_name][1]:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined subroutine '{subroutine_name}' in class '{class_name}'")
        elif self.defined_classes[class_name][1][subroutine_name][0] not in ["constructor", "function", "method"]:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' n_args was not set")
        else:
            return self.defined_classes[class_name][1][subroutine_name][0]
    
    def get_subroutine_is_void(self, class_name, subroutine_name):
        if subroutine_name not in self.defined_classes[class_name][1]:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined subroutine '{subroutine_name}' in class '{class_name}'")
        elif self.defined_classes[class_name][1][subroutine_name][1] not in [False, True]:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' is_void was not set")
        else:
            return self.defined_classes[class_name][1][subroutine_name][1]
    
    def get_subroutine_n_args(self, class_name, subroutine_name):
        if subroutine_name not in self.defined_classes[class_name][1]:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined subroutine '{subroutine_name}' in class '{class_name}'")
        elif self.defined_classes[class_name][1][subroutine_name][2] == -1:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' n_args was not set")
        else:
            return self.defined_classes[class_name][1][subroutine_name][2]

    def get_subroutine_n_locals(self, class_name, subroutine_name):
        if subroutine_name not in self.defined_classes[class_name][1]:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, undefined subroutine '{subroutine_name}' in class '{class_name}'")
        elif self.defined_classes[self.class_name][1][self.subroutine_name][3] == -1:
            raise ValueError(f"(Maybe a compiler error) File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' n_locals was not set")
        else:
            return self.defined_classes[self.class_name][1][self.subroutine_name][3]

    def comment_keyword(self, keyword):
        if self.tokenizer.tokenType() != "keyword" or self.tokenizer.keyword() != keyword:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a '{keyword}', but got '{self.tokenizer.token()}'")
        self.current_statement += keyword
        self.current_statement += " "

    def comment_symbol(self, symbol):
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != symbol:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a '{symbol}', but got '{self.tokenizer.token()}'")
        self.current_statement += symbol
        self.current_statement += " "

    def comment_identifier(self):
        self.current_statement += self.tokenizer.identifier()
        self.current_statement += " "

    def comment_integer(self):
        self.current_statement += str(self.tokenizer.intVal())
        self.current_statement += " "

    def comment_string(self):
        self.current_statement += self.tokenizer.stringVal()
        self.current_statement += " "
    
    def write_comment(self):
        self.writer.write_comment(self.current_statement)
        self.current_statement = f"line {self.tokenizer.currentLine()}: "
        # pass
