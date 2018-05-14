import logging

PREFIX = 'bot'

logging.basicConfig(filename=PREFIX+'.log',level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def default():
    logger = logging.getLogger(PREFIX)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    fh = logging.FileHandler(PREFIX+'.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

# logged class buitlin
class LoggedClass:
    @staticmethod
    def getLogger(name):
        if __name__ == '__main__':
            module = 'main'
        else:
            module = __name__
        if name == None:
            n = ''
        else:
            module += '.'
            n = name
        return logging.getLogger(PREFIX+'.'+module+n)
    @property
    def logger(self):
        if self.__module__ == '__main__':
            module = ''
        else:
            module = self.__module__ + '.'
        name = self.__class__.__name__
        return logging.getLogger(PREFIX+'.'+module+name)
