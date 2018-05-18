from .core import HTTPResponseData
import os
import os.path

PATH = os.path.join(os.getcwd(),'images/')


def handle(path,headers,data):
    file_path = os.path.join(PATH,path)
    if os.isfile(file_path):
        file_data = read_bytes(file_path)
        response = HTTPResponseData(200, parse_path(file_path), file_data)
    else:
        response = HTTPResponseData(404, 'text/html', '')
    return response


def read_bytes(filename):
    with open(filename, 'rb') as file:
        content = file.read()
    return content


def parse_path(file):
    if file.endswith('.png'):
        type = 'image/png'
    elif file.endswith('.txt'):
        type = 'text/raw'
    else:
        type = 'text/html'
    return type
