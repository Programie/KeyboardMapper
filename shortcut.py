from typing import Dict

from PySide2.QtCore import QSettings


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
        self.key = None
        self.action = None
        self.data = None
        self.name = None

    def __str__(self):
        return self.name

    @staticmethod
    def new_from_config(section, settings: QSettings):
        shortcut = Shortcut()
        shortcut.key = int(section)
        shortcut.action = settings.value("action")
        shortcut.data = settings.value("data")
        shortcut.name = settings.value("name")

        return shortcut

    def to_config(self, settings: QSettings):
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


class Shortcuts:
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
        settings = QSettings(self.filename, QSettings.IniFormat)

        self.clear()

        for section in settings.childGroups():
            settings.beginGroup(section)
            self.add(Shortcut.new_from_config(section, settings))
            settings.endGroup()

    def save(self):
        settings = QSettings(self.filename, QSettings.IniFormat)

        for shortcut in self.list:
            settings.beginGroup(shortcut.key)
            shortcut.to_config(settings)
            settings.endGroup()
