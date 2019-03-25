import os
import shutil
import subprocess
from threading import Thread
from typing import Dict

import pyperclip
import yaml
from PySide2 import QtCore

from lib.desktopfiles import DesktopFile
from lib.xtestwrapper import XTestWrapper

translate = QtCore.QCoreApplication.translate


class Action:
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title


class Actions:
    LAUNCH_APPLICATION = Action("launchApplication", translate("shortcut_action", "Launch application"))
    EXECUTE_COMMAND = Action("executeCommand", translate("shortcut_action", "Execute command"))
    OPEN_FOLDER = Action("openFolder", translate("shortcut_action", "Open folder"))
    INPUT_TEXT = Action("inputText", translate("shortcut_action", "Input text"))
    INPUT_KEY_SEQUENCE = Action("inputKeySequence", translate("shortcut_action", "Input key sequence"))
    LOCK_KEYS = Action("lockKeys", translate("shortcut_action", "Lock keys"))

    ACTIONS = [LAUNCH_APPLICATION, EXECUTE_COMMAND, OPEN_FOLDER, INPUT_TEXT, INPUT_KEY_SEQUENCE, LOCK_KEYS]

    @staticmethod
    def get(name: str):
        for action in Actions.ACTIONS:
            if action.name == name:
                return action


class ExecThread(Thread):
    def __init__(self, shortcut: "Shortcut"):
        super().__init__()

        self.shortcut = shortcut

    def run(self):
        if self.shortcut.action == Actions.LAUNCH_APPLICATION.name:
            temp_desktop_file = os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "keyboard-mapper-tmp.desktop")

            try:
                shutil.copy(self.shortcut.data, temp_desktop_file)
            except Exception as exception:
                self.show_execution_error(str(exception))
                return

            try:
                subprocess.check_output(["gtk-launch", os.path.basename(temp_desktop_file)], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exception:
                self.show_execution_error(exception.output)

            os.remove(temp_desktop_file)
        elif self.shortcut.action == Actions.EXECUTE_COMMAND.name:
            try:
                subprocess.check_output(self.shortcut.data, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exception:
                self.show_execution_error(exception.output)
        elif self.shortcut.action == Actions.OPEN_FOLDER.name:
            try:
                subprocess.check_call(["xdg-open", self.shortcut.data], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exception:
                self.show_execution_error(exception.output)
        elif self.shortcut.action == Actions.INPUT_TEXT.name:
            pyperclip.copy(self.shortcut.data)
            XTestWrapper().send_combination(["Control_L", "V"])
        elif self.shortcut.action == Actions.INPUT_KEY_SEQUENCE.name:
            xtest_wrapper = XTestWrapper()

            for combination in self.shortcut.data.split(" "):
                xtest_wrapper.send_combination(combination.split("+"))
        elif self.shortcut.action == Actions.LOCK_KEYS.name:
            Shortcuts.instance.lock_keys.emit()

    def show_execution_error(self, error_details: str):
        message = [
            translate("shortcut_error", "An error occurred while executing the action for key {} on device {}!").format(self.shortcut.key, self.shortcut.device),
            "",
            translate("shortcut_error", "Action: {}").format(self.shortcut.get_action_name())
        ]

        if error_details is not None and error_details != "":
            if isinstance(error_details, bytes):
                error_details = error_details.decode()

            message.append("")
            message.append(error_details)

        Shortcuts.instance.execution_error.emit("\n".join(message))


class Shortcut:
    def __init__(self):
        self.device: str = None
        self.key: int = None
        self.action: str = None
        self.data: str = None
        self.name: str = None

    def __str__(self):
        return self.name

    @staticmethod
    def new_from_config(shortcut_properties):
        shortcut = Shortcut()
        shortcut.device = shortcut_properties["device"]
        shortcut.key = int(shortcut_properties["key"])
        shortcut.action = shortcut_properties["action"]
        shortcut.data = shortcut_properties["data"]
        shortcut.name = shortcut_properties["name"]

        return shortcut

    def to_config(self):
        return {
            "device": self.device,
            "key": self.key,
            "name": self.name,
            "action": self.action,
            "data": self.data
        }

    def get_action_name(self):
        if self.action == Actions.LAUNCH_APPLICATION.name:
            desktop_file = DesktopFile.read(self.data)

            if desktop_file.name is None:
                application_name = self.data
            else:
                application_name = desktop_file.name

            return "{}: {}".format(Actions.LAUNCH_APPLICATION.title, application_name)
        elif self.action == Actions.LOCK_KEYS.name:
            return Actions.LOCK_KEYS.title
        else:
            return "{}: {}".format(Actions.get(self.action).title, self.data)

    def execute(self):
        thread = ExecThread(self)

        # Do not wait for the thread once Keyboard Mapper termination has been requested, just stop it
        thread.setDaemon(True)

        thread.start()


class Shortcuts(QtCore.QObject):
    instance: "Shortcuts" = None
    lock_keys = QtCore.Signal()
    execution_error = QtCore.Signal(str)

    def __init__(self, filename: str):
        super().__init__()

        Shortcuts.instance = self

        self.execution_error.connect(lambda message: print(message))

        self.list: Dict[Shortcut] = {}
        self.filename = filename

    def add(self, shortcut: Shortcut):
        self.list[(shortcut.device, shortcut.key)] = shortcut

    def remove_by_device_key(self, device_name: str, key):
        self.list.pop((device_name, key), None)

    def get_by_device_key(self, device_name: str, key):
        return self.list.get((device_name, key))

    def get_list(self):
        return self.list

    def clear(self):
        self.list.clear()

    def load(self):
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r") as file:
            data = yaml.safe_load(file)

        self.clear()

        for shortcut in data:
            self.add(Shortcut.new_from_config(shortcut))

    def load_legacy(self, filename, device):
        if not os.path.exists(filename):
            return

        settings = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)

        for section in settings.childGroups():
            settings.beginGroup(section)
            shortcut = Shortcut()
            shortcut.device = device
            shortcut.key = int(section)
            shortcut.name = settings.value("name")
            shortcut.action = settings.value("action")
            shortcut.data = settings.value("data")
            settings.endGroup()
            self.add(shortcut)

    def save(self):
        data = []

        for index in self.list:
            shortcut = self.list[index]
            data.append(shortcut.to_config())

        with open(self.filename, "w") as file:
            yaml.dump(data, file, default_flow_style=False)
