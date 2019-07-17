import json
import urllib.parse as parse

def unquote(data):
    if type(data) is dict:
        for key in data:
            data[key] = unquote(data[key])
    elif type(data) is list:
        for i in range(0,len(data)):
            data[i] = unquote(data[i])
    elif type(data) is str:
        data = parse.unquote_plus(data)
    return data

def main():
    path = input('Enter path to file: ')

    file = open(path,'rb')
    c = str(file.read(),encoding='utf-8')
    file.close()

    print(c)

    user = input('Continue (y)?')

    if user != 'y':
        return 0

    j = json.loads(c)

    j = unquote(j)
    t = json.dumps(j)

    try:
        print(t)
    except UnicodeDecodeError:
        print('Unable to display text')
    user = input('Write (y)?')

    if user != 'y':
        return 0

    file = open(path,'w')
    file.write(t)
    file.close()
    return 0

if __name__ == '__main__':
    main()
