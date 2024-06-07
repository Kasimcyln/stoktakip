import threading
from threading import Thread
import time
import sqlite3



class Job(threading.Thread):
    def _init_(self, *args, **kwargs):
        super(Job, self)._init_(*args, **kwargs)
        self.type = type
        self.__flag = threading.Event()  # The flag used to pause the thread
        self.__flag.set()  # Set to True
        self.__running = threading.Event()  # Used to stop the thread identification
        self.__running.set()  # Set running to True
        self.conn = sqlite3.connect('stok_takip.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS stoklar
                          (urun_adi TEXT,
                           miktar INTEGER,
                           alis_tarihi TEXT,
                           alis_fiyati REAL,
                           satis_tarihi TEXT,
                           satis_fiyati REAL,
                           kimden_alindi TEXT,
                           kime_satildi TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS islem_gecmisi
                          (id INTEGER PRIMARY KEY,
                           islem_tipi TEXT,
                           urun_adi TEXT,
                           miktar INTEGER,
                           tarih TEXT,
                           fiyat REAL,
                           kisi TEXT)''')
        self.conn.commit()

    def run(self):
        while self.__running.is_set():
            self.__flag.wait()  # return immediately when it is True, block until the internal flag is True when it is False
            print(time.time())
            time.sleep(1)

    def pause(self):
        self.__flag.clear()  # Set to False to block the thread

    def resume(self):
        self.__flag.set()  # Set to True, let the thread stop blocking

    def stop(self):
        self.__flag.set()  # Resume the thread from the suspended state, if it is already suspended
        self.__running.clear()  # Set to False


class Watcher(Thread):
    def _init_(self, worker: Job):
        super()._init_()
        self.worker = worker

    def run(self) -> None:
        while True:
           return

# if _name_ == '_main_':
#     wrk = Job()
#     wtc = Watcher(wrk)
#
#     wtc.start()
#     wrk.start()