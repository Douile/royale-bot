import os
from os.path import join


def count_lines(lines):
    file_line_count = 0
    file_blank_line_count = 0
    file_comment_line_count = 0

    for line in lines:
        file_line_count += 1

        lineWithoutWhitespace = line.strip()
        if not lineWithoutWhitespace:
            file_blank_line_count += 1
        elif lineWithoutWhitespace.startswith('#'):
            file_comment_line_count += 1

    file_code_line_count = file_line_count - file_blank_line_count - file_comment_line_count
    return file_code_line_count


def read_lines(file):
    f = open(file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def count_file(file):
    return count_lines(read_lines(file))


def count_project():
    line_count = 0
    for root, dirs, files in os.walk(os.getcwd()):
        for name in files:
            fullpath = join(root, name)
            if '.ignore' not in fullpath and '.git' not in fullpath:
                if fullpath.endswith('.py'):
                    line_count += count_file(join(root, name))
    return line_count
