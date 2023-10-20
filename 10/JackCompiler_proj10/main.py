import os

file_path = "/path/to/myfile.txt"

file_name = os.path.splitext(file_path)[0]
print(file_name)  # 输出 "/path/to/myfile"

file_name = os.path.basename(file_path)
print(file_name)  # 输出 "myfile.txt"

with open("test.txt", "w") as f:
    f.write("Hello\tworld!\n")
    f.write("\t123\n")
    n_tabs = 2
    tabs = "\t" * n_tabs
    f.write(tabs + "Hello\tworld!")
