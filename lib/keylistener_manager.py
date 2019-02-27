import enum
import os
from typing import List

from lib.keylistener import KeyListener
from lib.shortcut import Shortcuts, Actions, Shortcut


class AllowedActions(enum.Enum):
    NONE = 0
    LOCK_KEYS = 1
    ALL = 2


class KeyListenerManager:
    def __init__(self, devices_base_dir: str, shortcuts: Shortcuts):
        self.devices_base_dir = devices_base_dir
        self.input_devices: List[str] = []
        self.key_listener_threads: List[KeyListener] = []
        self.shortcuts = shortcuts
        self.allowed_actions = AllowedActions.ALL

    def set_device_files(self, input_devices: List[str]):
        self.input_devices = input_devices
        self.restart_threads()

    def restart_threads(self):
        self.stop_threads()

        self.key_listener_threads = []

        for input_device in self.input_devices:
            key_listener = KeyListener(os.path.join(self.devices_base_dir, input_device))
            key_listener.setDaemon(True)
            key_listener.start()
            self.key_listener_threads.append(key_listener)

        self.use_default_event_handler()

    def stop_threads(self):
        for key_listener in self.key_listener_threads:
            key_listener.stop()

    def set_event_handler(self, event_handler: callable):
        for key_listener in self.key_listener_threads:
            key_listener.set_event_handler(self.get_event_handler_function(key_listener, event_handler))

    def use_default_event_handler(self):
        self.set_event_handler(self.handle_key_press)

    @staticmethod
    def get_event_handler_function(key_listener, event_handler):
        return lambda key_code: event_handler(os.path.basename(key_listener.device_file), key_code)

    def handle_key_press(self, input_device_name, key_code):
        # Skip if disabled
        if self.allowed_actions == AllowedActions.NONE:
            return

        # Skip if shortcut not configured
        shortcut: Shortcut = self.shortcuts.get_by_device_key(input_device_name, key_code)
        if shortcut is None:
            return

        # Skip if keys are locked and this shortcut is not used to lock/unlock keys
        if self.allowed_actions == AllowedActions.LOCK_KEYS and shortcut.action != Actions.LOCK_KEYS.name:
            return

        shortcut.execute()
