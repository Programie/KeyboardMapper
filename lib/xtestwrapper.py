from typing import List

from Xlib import X, XK, keysymdef
from Xlib.display import Display
from Xlib.ext import xtest

# Load all key symbol definition modules
for module in keysymdef.__all__:
    XK.load_keysym_group(module)


class XKeys:
    @staticmethod
    def get_keys():
        for key in XK.__dict__:
            if key.startswith("XK_"):
                yield key[3:]


class XTestWrapper:
    def __init__(self):
        self.display = Display()
        self.root = self.display.screen().root

    def press(self, window, key, event_type):
        # Generate the correct keycode
        keysym = XK.string_to_keysym(key)
        keycode = self.display.keysym_to_keycode(keysym)

        # Send a fake keypress via xtest
        xtest.fake_input(window, event_type, keycode)

    def send_combination(self, keys: List[str]):
        self.root.ungrab_key(10, X.AnyModifier)
        window = self.display.get_input_focus()._data["focus"]

        for key in keys:
            self.press(window, key, X.KeyPress)

        for key in reversed(keys):
            self.press(window, key, X.KeyRelease)

        self.display.flush()
        self.display.sync()

        # fast forward those two events,this seems a bit hacky,
        # what if there is another key event coming in at that exact time?
        while self.display.pending_events():
            self.display.next_event()

        self.root.grab_key(10, X.AnyModifier, True, X.GrabModeSync, X.GrabModeSync)
