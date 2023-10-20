class VMWriter:
    def __init__(self, output_file):
        # 初始化 VMWriter
        self.output_file = output_file

    def open(self):
        # 打开输出文件
        with open(self.output_file, "w") as f:
            f.write(f"// File name: {self.output_file}\n")
    
    def write_comment(self, comment):
        # 生成注释
        with open(self.output_file, "a") as f:
            f.write("// " + comment + "\n")

    def write_push(self, segment, index):
        # 生成 push 命令
        with open(self.output_file, "a") as f:
            f.write("push " + segment + " " + str(index) + "\n")

    def write_pop(self, segment, index):
        # 生成 pop 命令
        with open(self.output_file, "a") as f:
            f.write("pop " + segment + " " + str(index) + "\n")

    def write_arithmetic(self, command):
        # 生成算术命令
        with open(self.output_file, "a") as f:
            f.write(command + "\n")

    def write_label(self, label):
        # 生成 label 命令
        with open(self.output_file, "a") as f:
            f.write("label " + label + "\n")

    def write_goto(self, label):
        # 生成 goto 命令
        with open(self.output_file, "a") as f:
            f.write("goto " + label + "\n")

    def write_if(self, label):
        # 生成 if 命令
        with open(self.output_file, "a") as f:
            f.write("if-goto " + label + "\n")

    def write_call(self, name, n_args):
        # 生成 call 命令
        with open(self.output_file, "a") as f:
            f.write("call " + name + " " + str(n_args) + "\n")

    def write_function(self, name, n_locals):
        # 生成 function 命令
        with open(self.output_file, "a") as f:
            f.write("function " + name + " " + str(n_locals) + "\n")

    def write_return(self):
        # 生成 return 命令
        with open(self.output_file, "a") as f:
            f.write("return\n")

    def close(self):
        # 关闭输出文件
        pass
