import tkinter as tk
from tkinter import filedialog
import json
import os.path

VALID_LOCALE = ['manifest.json','messages.json']

def selectDir():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(initialdir = '..\\', title = 'Select locale folder')

def selectLocale():
    path = selectDir()
    for item in VALID_LOCALE:
        if not os.path.isfile(os.path.join(path,item)):
            raise ValueError('Not a valid locale directory does not include '+item)
    return path

def selectLocaleAlways():
    while 1:
        try:
            path = selectLocale()
            break
        except:
            print('Please choose a valid directory')
    return path

class Locale:
    def __init__(self,*,manifest={},messages={}):
        self.manifest = manifest
        self.messages = messages

def loadJson(path):
    with open(path,'rb') as file:
        c = str(file.read(),encoding='utf-8')
    return json.loads(c)

def loadLocale(path):
    manifest = loadJson(os.path.join(path,'manifest.json'))
    messages = loadJson(os.path.join(path,'messages.json'))
    return Locale(manifest=manifest,messages=messages)

def main():
    print('Choose locale 1')
    locale_1 = loadLocale(selectLocaleAlways())
    print('Selected locale '+locale_1.manifest.get('name'))
    print('Choose locale 2')
    locale_2 = loadLocale(selectLocaleAlways())
    print('Selected locale '+locale_2.manifest.get('name'))
    print('Locale 1 ({0}) has extra keys: '.format(locale_1.manifest.get('name_en')))
    for key in locale_1.messages:
        if not key in locale_2.messages:
            print('\t'+key)
    print('Locale 2 ({0}) has extra keys: '.format(locale_2.manifest.get('name_en')))
    for key in locale_2.messages:
        if not key in locale_1.messages:
            print('\t'+key)

if __name__ == '__main__':
    main()
