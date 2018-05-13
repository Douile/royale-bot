import os
from os.path import join


def count_lines(lines):
    nb_lines = 0
    docstring = False
    for line in lines:
        line = line.strip()

        if line == "" \
           or line.startswith("#") \
           or docstring and not (line.startswith('"""') or line.startswith("'''"))\
           or (line.startswith("'''") and line.endswith("'''") and len(line) > 3)\
           or (line.startswith('"""') and line.endswith('"""') and len(line) > 3):
            continue

        # this is either a starting or ending docstring
        elif line.startswith('"""') or line.startswith("'''"):
            docstring = not docstring
            continue
        else:
            nb_lines += 1
    return nb_lines


def read_lines(file):
    f = open(file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def count_file(file):
    return count_lines(read_lines(file))


def count_project():
    line_count = 0
    for root, dirs, files in os.walk('.', topdown=True):
        for name in files:
            if name.endswith('.py'):
                line_count += count_file(join(root, name))
    return line_count
