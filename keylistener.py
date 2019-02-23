import os
import struct
import sys
import time
from select import select
from threading import Thread


class KeyListener(Thread):
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    def __init__(self, event_handler: callable, device_file: str = None):
        super().__init__()

        self.device_file = device_file
        self.event_handler = event_handler
        self.initial_event_handler = event_handler
        self.reload = False

    def set_event_handler(self, event_handler: callable):
        self.event_handler = event_handler

    def restore_event_handler(self):
        self.event_handler = self.initial_event_handler

    def set_device_file(self, device_file):
        self.device_file = device_file
        self.reload = True

    def run(self):
        while True:
            # Skip reading the file if no device configured yet
            if self.device_file is None:
                time.sleep(1)
                continue

            if not os.path.exists(self.device_file) or not os.access(self.device_file, os.R_OK):
                time.sleep(1)
                continue

            try:
                self.read_file()
            except Exception as exception:
                print(exception, file=sys.stderr)

            time.sleep(1)

    def read_file(self):
        with open(self.device_file, "rb", buffering=0) as file:
            while True:
                # If restart flag is set, break the loop to restart reading the file (e.g. if file path has changed)
                if self.reload:
                    self.reload = False
                    break

                # Wait for input (file.read() would block)
                r, w, x = select([file], [], [], 0)
                if not len(r):
                    continue

                (time_sec, time_usec, event_type, code, value) = struct.unpack(self.FORMAT, file.read(self.EVENT_SIZE))

                # Skip non-key press/release events (type 1 = key press/release event)
                if event_type != 1:
                    continue

                # Only handle key releases
                # value 0 = key released
                # value 1 = key pressed
                if value != 0:
                    continue

                self.event_handler(code)
