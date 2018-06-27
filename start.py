import threading
import os

class MyThread:
    def __init__(self, filename):
        self.name = filename
    def run(self):
        os.system('python {}'.format(self.name))

threads = ['bot.py','autoupdates.py']

for filename in threads:
    thread = MyThread(filename)
    threading.Thread(target=thread.run).start()
