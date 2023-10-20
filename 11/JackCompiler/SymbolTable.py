class SymbolTable:
    def __init__(self):
        # 初始化符号表
        self.table = {}
        self.indexes = {"static": 0, "field": 0, "argument": 0, "local": 0}  # 下一个索引

    def define(self, name, type_, kind):
        # 定义一个新的符号
        if name in self.table:
            return False
        self.table[name] = {"type": type_, "kind": kind, "index": self.indexes[kind]}
        self.indexes[kind] += 1
        return True
    
    def in_table(self, name):
        # 判断一个符号是否在符号表中
        return name in self.table

    def var_count(self, kind):
        # 获取指定种类的符号数量
        return self.indexes[kind]

    # to do: ValueError
    def kind_of(self, name):
        # 获取指定名称的符号的种类
        if name in self.table:
            return self.table[name]["kind"]
        else:
            return None

    def type_of(self, name):
        # 获取指定名称的符号的类型
        if name in self.table:
            return self.table[name]["type"]
        else:
            return None

    def index_of(self, name):
        # 获取指定名称的符号的索引
        if name in self.table:
            return self.table[name]["index"]
        else:
            return None
