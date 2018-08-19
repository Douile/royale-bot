import os
import threading

THREADS = 3

class BotThread:
    def __init__(self, shard_id, shard_count):
        self.shard_id = shard_id
        self.shard_count = shard_count
    def run(self):
        os.system('python bot.py {} {}'.format(self.shard_id,self.shard_count))


if __name__ == '__main__':
    for i in range(THREADS):
        thread = BotThread(i,THREADS)
        threading.Thread(target=thread.run).start()
