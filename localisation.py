import os
import os.path
import json
import logging
from memory_profiler import profile

class FormatMap(dict):
    def __missing__(self, key):
        return '{'+key+'}'
class LocaleResponse:
    def __init__(self,*,message='',description=None,lang=None):
        self.message = message
        self.description = description
        self.lang = lang
        self.variables = []
        self.parsed = False
        self.parseVariables()
    def parseVariables(self):
        if self.parsed:
            self.variables = []
        start = None
        end = None
        type = 'text'
        for i in range(0,len(self.message)):
            char = self.message[i]
            if char == '{':
                if start is None:
                    start = i+1
                else:
                    pass
            elif char == '}' and start is not None:
                end = i
                text = self.message[start:end]
                self.variables.append(self.Variable(name=text,type=type))
                start = None
                end = None
                type = 'text'
            elif char == ';' and start is not None:
                type = self.message[start:i]
                start = i+1
        self.parsed = True
    class Variable:
        def __init__(self,*,name='',type='text'):
            self.name = name
            self.type = type
        def __str__(self):
            return '{'+self.type+';'+self.name+'}'
        def formattable(self):
            if self.type == 'channel':
                text = '<#{0}>'
            elif self.type == 'user':
                text = '<@{0}>'
            elif self.type == 'link':
                text = '<{0}>'
            elif self.type == 'code':
                text = '`{0}`'
            elif self.type == 'bold':
                text = '**{0}**'
            else:
                text = '{0}'
            return text.format('{'+self.name+'}')
    def formattable(self):
        if not self.parsed:
            self.parseVariables()
        text = self.message
        for variable in self.variables:
            text = text.replace(str(variable),variable.formattable())
        return text
    def format(self,values):
        values = FormatMap(values)
        text = self.formattable()
        self.message = text.format_map(values)
        return self.message
    def __str__(self):
        return self.message
class Locale(dict):
    def __init__(self,*args,info={},lang=None):
        super().__init__(*args)
        self.lang = lang
        self.name = info.get('name')
        self.nameEn = info.get('name_en')
        self.author = info.get('author')
        self.authorName = info.get('author_name')
    @profile
    def getMessage(self,key):
        data = self.get(key)
        if data is not None:
            resp = LocaleResponse(message=data.get('message'),lang=self.lang)
            resp.format({})
        else:
            resp = LocaleResponse(msesage='Message not set',lang=self.lang)
        return resp
    @profile
    def getFormattedMessage(self,key,**variables):
        data = self.get(key,)
        if data is not None:
            resp = LocaleResponse(message=data.get('message'),lang=self.lang)
            resp.format(variables)
        else:
            resp = LocaleResponse(msesage='Message not set',lang=self.lang)
        return resp
    @profile
    def getInfo(self):
        return self.LocaleInfo(lang=self.lang,name=self.name,nameEn=self.nameEn,author=self.author,authorName=self.authorName)
    class LocaleInfo:
        def __init__(self,*,lang=None,name=None,nameEn=None,author=None,authorName=None):
            self.lang = lang
            self.name = name
            self.nameEn = nameEn
            self.author = author
            self.authorName = authorName
class LocaleContainer(dict):
    def __init__(self):
        super().__init__({})
        self.defaultLang = None
        self.globalVars = {}
    def setDefault(self,lang):
        self.defaultLang = lang
    def setGlobals(self,data):
        self.globalVars = data
    def addLocale(self,lang,info,data):
        self[lang] = Locale(data,info=info,lang=lang)
        if self.defaultLang is None:
            self.defaultLang = lang
    def getMessage(self,key,lang=None):
        if lang is None:
            lang = self.defaultLang
        res = self[lang].getMessage(key)
        return str(self.applyGlobals(res))
    def getFormattedMessage(self,key,lang=None,**variables):
        if lang is None:
            lang = self.defaultLang
        res = self[lang].getFormattedMessage(key,**variables)
        return str(self.applyGlobals(res))
    def applyGlobals(self,response):
        response.message = response.message.format_map(FormatMap(self.globalVars))
        return response
    def getLocales(self):
        locales = []
        for key in self:
            locales.append(self[key].getInfo())
        return locales

locales = LocaleContainer()

def readJson(filename):
    f = open(filename,'r')
    c = f.read()
    f.close()
    try:
        j = json.loads(c)
    except json.JSONDecodeError:
        j = {}
    return j

def loadLocales():
    global locales
    logger = logging.getLogger('locales')
    locales_dir = os.path.join(os.getcwd(),'_locales')
    if os.path.isdir(locales_dir):
        locale_names = [x[0] for x in os.walk(locales_dir)]
        for locale_path in locale_names:
            path = os.path.join(locales_dir,locale_path,'messages.json')
            if os.path.isfile(path):
                data = readJson(path)
            else:
                data = None
                logger.warn('No messages.json found for %s',locale_path)
            path = os.path.join(locales_dir,locale_path,'manifest.json')
            if os.path.isfile(path):
                info = readJson(path)
            else:
                info = None
                logger.warn('No manifest.json found for %s',locale_path)
            if data is not None:
                split = locale_path.split('/')
                locale_name = split[-1]
                locales.addLocale(locale_name,info,data)
                logger.info('Loaded locale %s',locale_name)
        path = os.path.join(locales_dir,'globals.json')
        if os.path.isfile(path):
            data = readJson(path)
            locales.setGlobals(data)
            logger.info('Global variables set')
        else:
            logger.info('No globals set')
    else:
        logger.warn('No locales folder found')

getMessage = locales.getMessage
getFormattedMessage = locales.getFormattedMessage
getLocales = locales.getLocales
setDefault = locales.setDefault

class PreMessage:
    def __init__(self,name,**formatting):
        self.name = name
        self.formatting = formatting
    def __str__(self):
        return locales.getFormattedMessage(self.name,**self.formatting)
    def getMessage(self,lang=None):
        return locales.getFormattedMessage(self.name,lang=lang,**self.formatting)

def is_pre(item):
    if type(item) is PreMessage:
        return True
    return False
