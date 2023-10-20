class CompilationEngine:
    def __init__(self, tokenizer, input_file, token_output_file, output_file):
        self.tokenizer = tokenizer
        self.file_name = input_file
        self.token_output_file = token_output_file
        self.output_file = output_file
        self.indent_level = 0  # 缩进层数
        self.have_return = False  # 当前subroutine是否有return语句
        self.subroutine_name = None  # 当前subroutine的名字
        self.write_token = False  # 上一个写入是否为token
        self.write_first_tag = True  # 是否为第一个tag
    
    def compile(self):
        with open(self.token_output_file, "w") as t, open(self.output_file, "w") as f:
            t.write("<tokens>\n")
        while self.tokenizer.has_more_tokens():
            self.compile_class()
        with open(self.token_output_file, "a") as t, open(self.output_file, "a") as f:
            f.write("\n")
            t.write("</tokens>\n")

    def compile_class(self):  # at last
        # class: 'class' className '{' classVarDec* subroutineDec* '}'
        self.advance("keyword", "class")
        self.write_tag_open("class")
        self.write_keyword("class")
        self.advance("identifier")
        self.write_identifier()
        self.advance("symbol", "{")
        self.write_symbol("{")
        self.try_advance("Unfinished class")
        # classVarDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["static", "field"]:
            self.compile_class_var_dec()
            self.try_advance("Expected a '}' in class")
        # subroutineDec
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["constructor", "function", "method"]:
            self.compile_subroutine()
            self.try_advance("Expected a '}' in class")
        self.write_symbol("}")
        self.write_tag_close("class")

    def compile_class_var_dec(self):  # at last
        # classVarDec: ('static'|'field') type varName (',' varName)* ';'
        self.write_tag_open("classVarDec")
        self.write_keyword(self.tokenizer.keyword())
        self.try_advance("Expected a type in classVarDec")
        self.compile_type()
        self.advance("identifier")
        self.write_identifier()
        self.try_advance("Expected a ';' in classVarDec")
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.write_symbol(",")
            self.advance("identifier")
            self.write_identifier()
            self.try_advance("Expected a ';' in classVarDec")
        self.write_symbol(";")
        self.write_tag_close("classVarDec")

    def compile_subroutine(self):
        # subroutineDec: ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody
        self.write_tag_open("subroutineDec")
        self.have_return = False
        self.write_keyword(self.tokenizer.keyword())
        self.try_advance("Expected a type in subroutineDec")
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "void":
            self.write_keyword(self.tokenizer.keyword())
        else:
            self.compile_type()
        self.advance("identifier")
        self.write_identifier()
        self.subroutine_name = self.tokenizer.identifier()
        self.advance("symbol", "(")
        self.write_symbol("(")
        self.try_advance("Expected a parameter list in subroutineDec")
        self.compile_parameter_list()
        self.write_symbol(")")
        self.compile_subroutine_body()
        if self.have_return is False:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, subroutine '{self.subroutine_name}' has no return statement")
        self.write_tag_close("subroutineDec")

    def compile_parameter_list(self):  # at next
        # parameterList: ((type varName) (',' type varName)*)?
        self.write_tag_open("parameterList")
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            self.compile_type()
            self.advance("identifier")
            self.write_identifier()
            self.try_advance("Unfinished parameterList")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.write_symbol(",")
                self.try_advance("Unfinished parameterList")
        self.write_tag_close("parameterList")
    
    def compile_subroutine_body(self):  # at last
        # subroutineBody: '{' varDec* statements '}'
        self.write_tag_open("subroutineBody")
        self.advance("symbol", "{")
        self.write_symbol("{")
        self.try_advance("Unfinished subroutineBody")
        while self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "var":
            self.compile_var_dec()
            self.try_advance("Unfinished subroutineBody")
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != "}":
            self.compile_statements()
        self.write_symbol("}")
        self.write_tag_close("subroutineBody")

    def compile_var_dec(self):  # at last
        # varDec: 'var' type varName (',' varName)* ';'
        self.write_tag_open("varDec")
        self.write_keyword("var")
        self.try_advance("Expected a type in varDec")
        self.compile_type()
        self.advance("identifier")
        self.write_identifier()
        self.try_advance("Expected a ';' in varDec")
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
            self.write_symbol(",")
            self.advance("identifier")
            self.write_identifier()
            self.try_advance("Expected a ';' in varDec")
        self.write_symbol(";")
        self.write_tag_close("varDec")
    
    def compile_statements(self):  # at next
        # statements: statement*
        self.write_tag_open("statements")
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
                break  # return语句后面不应该再有语句
            else:
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid keyword '{keyword}'")
        self.write_tag_close("statements")

    def compile_let(self):  # at last
        # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
        self.write_tag_open("letStatement")
        self.write_keyword("let")
        self.advance("identifier")
        self.write_identifier()
        self.try_advance("Expected a '=' in letStatement")
        if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
            self.write_symbol("[")
            self.try_advance("Expected an expression in '[]'")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "]":
                raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected an expression in '[]'")
            self.compile_expression()
            self.write_symbol("]")
            self.advance("symbol", "=")
        self.write_symbol("=")
        self.try_advance("Expected an expression right of '=' in letStatement")
        self.compile_expression()
        self.write_symbol(";")
        self.write_tag_close("letStatement")

    def compile_if(self):  # at next
        # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        self.write_tag_open("ifStatement")
        self.write_keyword("if")
        self.advance("symbol", "(")
        self.write_symbol("(")
        self.try_advance("Expected an expression in '()'")
        self.compile_expression()
        self.write_symbol(")")
        self.advance("symbol", "{")
        self.write_symbol("{")
        self.try_advance("Expected a '}'")
        self.compile_statements()
        self.write_symbol("}")
        self.try_advance("Expected a '}' in Statements")
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() == "else":
            self.write_keyword("else")
            self.advance("symbol", "{")
            self.write_symbol("{")
            self.try_advance("Expected a '}'")
            self.compile_statements()
            self.write_symbol("}")
            self.try_advance("Expected a '}' in Statements")
        self.write_tag_close("ifStatement")

    def compile_while(self):  # at last
        # whileStatement: 'while' '(' expression ')' '{' statements '}'
        self.write_tag_open("whileStatement")
        self.write_keyword("while")
        self.advance("symbol", "(")
        self.write_symbol("(")
        self.try_advance("Expected an expression in '()'")
        self.compile_expression()
        self.write_symbol(")")
        self.advance("symbol", "{")
        self.write_symbol("{")
        self.try_advance("Expected a '}'")
        self.compile_statements()
        self.write_symbol("}")
        self.write_tag_close("whileStatement")

    def compile_do(self):  # at last
        # doStatement: 'do' subroutineCall ';'
        self.write_tag_open("doStatement")
        self.write_keyword("do")
        self.advance("identifier")
        self.write_identifier()
        self.try_advance("Expected a subroutineCall")
        self.compile_subroutine_call()
        self.advance("symbol", ";")
        self.write_symbol(";")
        self.write_tag_close("doStatement")

    def compile_return(self):  # at last
        # returnStatement: 'return' expression? ';'
        self.write_tag_open("returnStatement")
        self.write_keyword("return")
        self.try_advance("Expected an expression in returnStatement")
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ";":
            self.compile_expression()
        self.write_symbol(";")
        self.have_return = True
        self.write_tag_close("returnStatement")

    def compile_expression(self):  # at next
        # expression: term (op term)*
        self.write_tag_open("expression")
        self.compile_term()
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="]:
            self.write_symbol(self.tokenizer.symbol())
            self.tokenizer.advance()
            self.compile_term()
        self.write_tag_close("expression")

    def compile_term(self):  # at next
        # term: integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        self.write_tag_open("term")
        token_type = self.tokenizer.tokenType()
        if token_type == "integerConstant":
            # integerConstant
            self.write_integer()
            self.try_advance("Expected a ';'")
        elif token_type == "stringConstant":
            # stringConstant
            self.write_string()
            self.try_advance("Expected a ';'")
        elif token_type == "keyword" and self.tokenizer.keyword() in ["true", "false", "null", "this"]:
            # keywordConstant
            self.write_keyword(self.tokenizer.keyword())
            self.try_advance("Expected a ';'")
        elif token_type == "identifier":
            self.write_identifier()
            self.try_advance("Unfinished term")
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == "[":
                # varName[expression]
                self.write_symbol("[")
                self.try_advance("Expected an expression in '[]'")
                self.compile_expression()
                self.write_symbol("]")
                self.try_advance("Expected a ';'")
            elif self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() in ["(", "."]:
                # subroutineCall
                self.compile_subroutine_call()
                self.try_advance("Expected a ';'")
            else:
                # varName
                pass
        elif token_type == "symbol" and self.tokenizer.symbol() == "(":
            # (expression)
            self.write_symbol("(")
            self.try_advance("Expected a ')'")
            self.compile_expression()
            self.write_symbol(")")
            self.try_advance("Expected a ';'")
        elif token_type == "symbol" and self.tokenizer.symbol() in ["-", "~"]:
            # unaryOp term
            self.write_symbol(self.tokenizer.symbol())
            self.try_advance(f"Unfinished term {self.tokenizer.token()}")
            self.compile_term()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid term '{self.tokenizer.token()}'")
        self.write_tag_close("term")

    def compile_subroutine_call(self):  # at last
        # subroutineName(expressionList) | (className|varName).subroutineName(expressionList)
        # 默认已经读取了subroutineName
        while self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ".":
            self.write_symbol(".")
            self.advance("identifier")
            self.write_identifier()
            self.advance("symbol")
        self.write_symbol("(")
        self.try_advance("Expected an expressionList in '()'")
        self.compile_expression_list()
        self.write_symbol(")")

    def compile_expression_list(self):  # at next
        # expressionList: (expression (',' expression)*)?
        self.write_tag_open("expressionList")
        while self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != ")":
            self.compile_expression()
            if self.tokenizer.tokenType() == "symbol" and self.tokenizer.symbol() == ",":
                self.write_symbol(",")
                self.try_advance("Unfinished expressionList after ','")
        self.write_tag_close("expressionList")

    def compile_type(self):  # at last
        # _type: 'int'|'char'|'boolean'|className
        if self.tokenizer.tokenType() == "keyword" and self.tokenizer.keyword() in ["int", "char", "boolean"]:
            self.write_keyword(self.tokenizer.keyword())
        elif self.tokenizer.tokenType() == "identifier":
            self.write_identifier()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, invalid type '{self.tokenizer.token()}'")
    
    def advance(self, expected_token_type, expected_token=None):
        # 前进一个token，如果不是期望的token，抛出异常
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
        else:
            line_num = self.tokenizer.currentLine()
            if expected_token is None:
                raise ValueError(f"File {self.file_name}, in line {line_num}, expected a {expected_token_type}, but no more tokens")
            else:
                raise ValueError(f"File {self.file_name}, in line {line_num}, expected {expected_token_type} '{expected_token}', but no more tokens")

    def try_advance(self, errorMsg):
        # 前进一个token，如果没有更多token，抛出异常
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
        else:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, {errorMsg}, but no more tokens")

    def write_tag_open(self, tag):
        self.write_tag(tag, True)

    def write_tag_close(self, tag):
        self.write_tag(tag, False)

    def write_tag(self, tag, is_opening_tag):
        if is_opening_tag:
            indent = "  " * self.indent_level
            with open(self.output_file, "a") as f:
                if self.write_first_tag:
                    f.write(f"{indent}<{tag}>")
                    self.write_first_tag = False
                else:
                    f.write(f"\n{indent}<{tag}>")
            self.indent_level += 1
        else:
            self.indent_level -= 1
            indent = "  " * self.indent_level
            with open(self.output_file, "a") as f:
                if self.write_token:
                    f.write(f"</{tag}>")
                    self.write_token = False
                else:
                    f.write(f"\n{indent}</{tag}>")

    def write_keyword(self, keyword):
        self.write_tag("keyword", True)
        with open(self.token_output_file, "a") as t:
            t.write(f"<keyword> {keyword} </keyword>\n")
        with open(self.output_file, "a") as f:
            f.write(f" {keyword} ")
            self.write_token = True
        self.write_tag("keyword", False)

    def write_symbol(self, symbol):
        if self.tokenizer.tokenType() != "symbol" or self.tokenizer.symbol() != symbol:
            raise ValueError(f"File {self.file_name}, in line {self.tokenizer.currentLine()}, expected a '{symbol}' in subroutineDec, but got '{self.tokenizer.token()}'")
        self.write_tag("symbol", True)
        with open(self.token_output_file, "a") as t:
            t.write(f"<symbol> {symbol} </symbol>\n")
        with open(self.output_file, "a") as f:
            f.write(f" {symbol} ")
            self.write_token = True
        self.write_tag("symbol", False)

    def write_identifier(self):
        self.write_tag("identifier", True)
        with open(self.token_output_file, "a") as t:
            t.write(f"<identifier> {self.tokenizer.identifier()} </identifier>\n")
        with open(self.output_file, "a") as f:
            f.write(f" {self.tokenizer.identifier()} ")
            self.write_token = True
        self.write_tag("identifier", False)

    def write_integer(self):
        self.write_tag("integerConstant", True)
        with open(self.token_output_file, "a") as t:
            t.write(f"<integerConstant> {self.tokenizer.intVal()} </integerConstant>\n")
        with open(self.output_file, "a") as f:
            f.write(f" {self.tokenizer.intVal()} ")
            self.write_token = True
        self.write_tag("integerConstant", False)

    def write_string(self):
        self.write_tag("stringConstant", True)
        with open(self.token_output_file, "a") as t:
            t.write(f"<stringConstant> {self.tokenizer.stringVal()} </stringConstant>\n")
        with open(self.output_file, "a") as f:
            f.write(f" {self.tokenizer.stringVal()} ")
            self.write_token = True
        self.write_tag("stringConstant", False)
