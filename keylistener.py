import os
import struct
import time
from select import select
from threading import Thread

from config import Config
from shortcut import Shortcuts


class KeyListener(Thread):
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    restart = False
    keys_locked = False

    def run(self):
        while True:
            # Skip reading the file if no device configured yet
            if Config.keyboard_input_device is None:
                time.sleep(1)
                continue

            if not os.path.exists(Config.keyboard_input_device) or not os.access(Config.keyboard_input_device, os.R_OK):
                time.sleep(1)
                continue

            try:
                with open(Config.keyboard_input_device, "rb", buffering=0) as file:
                    while True:
                        # If restart flag is set, break the loop to restart reading the file (e.g. if file path has changed)
                        if KeyListener.restart:
                            KeyListener.restart = False
                            print("restart")
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

                        self.handle_key_press(code)

                print("eof")
            except:
                pass

            time.sleep(1)

    def handle_key_press(self, key_code):
        print(key_code)


if __name__ == "__main__":

    config_dir = os.path.join(os.path.expanduser("~"), ".config", "keyboard-mapper")

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    Config.filename = os.path.join(config_dir, "config.ini")
    Config.load()

    shortcuts = Shortcuts(os.path.join(config_dir, "shortcuts.ini"))
    shortcuts.load()

    key_listener = KeyListener()
    key_listener.setDaemon(True)
    key_listener.start()
    key_listener.join()
