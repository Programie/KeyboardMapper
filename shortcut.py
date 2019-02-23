import os
import shutil
import subprocess
from typing import Dict

import pyperclip
from PySide2 import QtCore

from xtestwrapper import XTestWrapper


class Action:
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title


class Actions:
    LAUNCH_APPLICATION = Action("launchApplication", "Launch application")
    EXECUTE_COMMAND = Action("executeCommand", "Execute command")
    OPEN_FOLDER = Action("openFolder", "Open folder")
    INPUT_TEXT = Action("inputText", "Input text")
    INPUT_KEY_SEQUENCE = Action("inputKeySequence", "Input key sequence")
    LOCK_KEYS = Action("lockKeys", "Lock keys")

    ACTIONS = [LAUNCH_APPLICATION, EXECUTE_COMMAND, OPEN_FOLDER, INPUT_TEXT, INPUT_KEY_SEQUENCE, LOCK_KEYS]

    @staticmethod
    def get(name: str):
        for action in Actions.ACTIONS:
            if action.name == name:
                return action


class Shortcut:
    def __init__(self):
        self.key: int = None
        self.action: str = None
        self.data: str = None
        self.name: str = None

    def __str__(self):
        return self.name

    @staticmethod
    def new_from_config(section, settings: QtCore.QSettings):
        shortcut = Shortcut()
        shortcut.key = int(section)
        shortcut.action = settings.value("action")
        shortcut.data = settings.value("data")
        shortcut.name = settings.value("name")

        return shortcut

    def to_config(self, settings: QtCore.QSettings):
        settings.setValue("action", self.action)
        settings.setValue("data", self.data)
        settings.setValue("name", self.name)

    def get_action_name(self):
        if self.action == Actions.LAUNCH_APPLICATION.name:
            return Actions.LAUNCH_APPLICATION.title
        elif self.action == Actions.LOCK_KEYS.name:
            return Actions.LOCK_KEYS.title
        else:
            return "{}: {}".format(Actions.get(self.action).title, self.data)

    def execute(self):
        if self.action == Actions.LAUNCH_APPLICATION.name:
            temp_desktop_file = os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "keyboard-mapper-tmp.desktop")
            shutil.copy(self.data, temp_desktop_file)
            subprocess.run(["gtk-launch", os.path.basename(temp_desktop_file)])
            os.remove(temp_desktop_file)
        elif self.action == Actions.EXECUTE_COMMAND.name:
            subprocess.run(self.data, shell=True)
        elif self.action == Actions.OPEN_FOLDER.name:
            subprocess.run(["xdg-open", self.data])
        elif self.action == Actions.INPUT_TEXT.name:
            pyperclip.copy(self.data)
            XTestWrapper().send_combination(["Control_L", "V"])
        elif self.action == Actions.INPUT_KEY_SEQUENCE.name:
            xtest_wrapper = XTestWrapper()

            for combination in self.data.split(" "):
                xtest_wrapper.send_combination(combination.split("+"))
        elif self.action == Actions.LOCK_KEYS.name:
            if Shortcuts.lock_keys_handler:
                Shortcuts.lock_keys_handler()


class Shortcuts:
    lock_keys_handler: callable = None

    def __init__(self, filename: str):
        self.list: Dict[Shortcut] = {}
        self.filename = filename

    def add(self, shortcut: Shortcut):
        self.list[shortcut.key] = shortcut

    def remove_by_key(self, key):
        self.list.pop(key, None)

    def get_by_key(self, key):
        return self.list.get(key)

    def get_list(self):
        return self.list

    def clear(self):
        self.list.clear()

    def load(self):
        settings = QtCore.QSettings(self.filename, QtCore.QSettings.IniFormat)

        self.clear()

        for section in settings.childGroups():
            settings.beginGroup(section)
            self.add(Shortcut.new_from_config(section, settings))
            settings.endGroup()

    def save(self):
        settings = QtCore.QSettings(self.filename, QtCore.QSettings.IniFormat)

        for index in self.list:
            shortcut = self.list[index]
            settings.beginGroup(str(shortcut.key))
            shortcut.to_config(settings)
            settings.endGroup()
