import threading
import os

class Watchdog:
    def __init__(self, timeout=3.0, on_timeout=None):
        self.timeout = timeout
        self.on_timeout = on_timeout if on_timeout is not None else (lambda: os._exit(1))
        self.timer = None

    def _timeout_handler(self):
        print(f"watchdog timeout !!!")
        self.on_timeout()

    def feed(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self._timeout_handler)
        self.timer.daemon = True
        self.timer.start()
