import os
import struct
from pathlib import Path

import sys
import time
from select import select
from threading import Thread


class KeyListener(Thread):
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    def __init__(self, device_file: Path, event_handler: callable = None):
        super().__init__()

        self.device_file = device_file
        self.event_handler = event_handler
        self.do_stop = False
        self.pressed_keys = set()

    def set_event_handler(self, event_handler: callable):
        self.event_handler = event_handler

    def run(self):
        while True:
            if not self.device_file.exists() or not os.access(self.device_file, os.R_OK):
                time.sleep(1)
                continue

            if self.do_stop:
                break

            try:
                self.read_file()
            except Exception as exception:
                print(exception, file=sys.stderr)

            time.sleep(1)

    def stop(self):
        self.do_stop = True

    def read_file(self):
        with self.device_file.open("rb", buffering=0) as file:
            while True:
                if self.do_stop:
                    break

                # Wait for input (file.read() would block)
                r, w, x = select([file], [], [], 0)
                if not len(r):
                    time.sleep(0.01)
                    continue

                (time_sec, time_usec, event_type, code, value) = struct.unpack(self.FORMAT, file.read(self.EVENT_SIZE))

                # Skip non-key press/release events (type 1 = key press/release event)
                if event_type != 1:
                    continue

                # value 0 = key released
                # value 1 = key pressed
                self.handle_key(code, bool(value))

    def handle_key(self, code: int, pressed: bool):
        if pressed:
            if code in self.pressed_keys:
                # handle_key() is executed multiple times while the key is still pressed due to non-blocking file read
                # Therefore, prevent triggering event handler multiple times if key code was already added to pressed keys
                return

            self.pressed_keys.add(code)
        else:
            self.pressed_keys.remove(code)

        if self.event_handler:
            self.event_handler(self.pressed_keys, pressed)
