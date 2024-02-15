import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Dict

import pyperclip
import yaml
from PyQt5 import QtCore, QtPrintSupport, QtGui

from lib.config import Config
from lib.desktopfiles import DesktopFile
from lib.utils import LengthUnit
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
            temp_desktop_file = Path("~/.local/share/applications/keyboard-mapper-tmp.desktop").expanduser()

            try:
                shutil.copy(self.shortcut.data, temp_desktop_file)
            except Exception as exception:
                self.show_execution_error(str(exception))
                return

            try:
                subprocess.check_output(["gtk-launch", temp_desktop_file.name], stderr=subprocess.STDOUT)
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


class Label:
    def __init__(self):
        self.icon_path: str = None
        self.width: int = None
        self.height: int = None
        self.background_color: str = None


class ShortcutKey(set):
    @staticmethod
    def from_string(string: str):
        key = ShortcutKey()

        for key_code in string.split("+"):
            key_code = key_code.strip()

            if not key_code:
                continue

            key.add(key_code)

        return key

    def __str__(self):
        return "+".join([str(key) for key in sorted(self)])


class Shortcut:
    def __init__(self):
        self.uuid: str = str(uuid.uuid1())
        self.device: str = None
        self.key: ShortcutKey = ShortcutKey()
        self.action: str = None
        self.data: str = None
        self.name: str = None
        self.label: Label = Label()
        self.executions: int = 0
        self.last_execution: datetime = None

    def __str__(self):
        return self.name

    @staticmethod
    def new_from_config(shortcut_properties):
        shortcut = Shortcut()
        shortcut.uuid = shortcut_properties.get("uuid", str(uuid.uuid1()))
        shortcut.device = shortcut_properties["device"]
        shortcut.key = ShortcutKey.from_string(str(shortcut_properties["key"]))
        shortcut.action = shortcut_properties["action"]
        shortcut.data = shortcut_properties["data"]
        shortcut.name = shortcut_properties["name"]

        # Deprecated, just loaded from old config format
        if "executions" in shortcut_properties and shortcut_properties["executions"]:
            shortcut.executions = int(shortcut_properties["executions"])
        else:
            shortcut.executions = 0

        # Deprecated, just loaded from old config format
        if "last_execution" in shortcut_properties and shortcut_properties["last_execution"]:
            shortcut.last_execution = datetime.fromtimestamp(int(shortcut_properties["last_execution"]))
        else:
            shortcut.last_execution = None

        if "label" in shortcut_properties and shortcut_properties["label"]:
            label_properties = shortcut_properties["label"]

            shortcut.label.icon_path = label_properties.get("icon_path")
            shortcut.label.width = label_properties.get("width")
            shortcut.label.height = label_properties.get("height")
            shortcut.label.background_color = label_properties.get("background_color")

        return shortcut

    def reinit(self):
        self.uuid = str(uuid.uuid1())
        self.executions = 0
        self.last_execution = None

    def add_tracking_data(self, data):
        if not data:
            return

        self.executions = int(data.get("executions", 0))

        last_execution = data.get("last_execution")
        if last_execution:
            self.last_execution = datetime.fromtimestamp(int(last_execution))

    def to_config(self):
        return {
            "uuid": self.uuid,
            "device": self.device,
            "key": str(self.key),
            "name": self.name,
            "action": self.action,
            "data": self.data,
            "label": {
                "icon_path": self.label.icon_path,
                "width": self.label.width,
                "height": self.label.height,
                "background_color": self.label.background_color
            }
        }

    def to_tracking_data(self):
        if self.last_execution:
            last_execution = self.last_execution.timestamp()
        else:
            last_execution = None

        return {
            "executions": self.executions,
            "last_execution": last_execution
        }

    def get_action_name(self):
        if self.action == Actions.LAUNCH_APPLICATION.name:
            desktop_file = DesktopFile.read(Path(self.data))

            if desktop_file.name is None:
                application_name = self.data
            else:
                application_name = desktop_file.name

            return "{}: {}".format(Actions.LAUNCH_APPLICATION.title, application_name)
        elif self.action == Actions.LOCK_KEYS.name:
            return Actions.LOCK_KEYS.title
        else:
            return "{}: {}".format(Actions.get(self.action).title, self.data)

    def last_execution_string(self):
        if not self.last_execution:
            return ""

        return self.last_execution.strftime("%c")

    def execute(self):
        self.executions += 1
        self.last_execution = datetime.now()

        thread = ExecThread(self)

        # Do not wait for the thread once Keyboard Mapper termination has been requested, just stop it
        thread.daemon = True

        thread.start()

        Shortcuts.instance.executed.emit(self)


class Shortcuts(QtCore.QObject):
    instance: "Shortcuts" = None
    lock_keys = QtCore.pyqtSignal()
    execution_error = QtCore.pyqtSignal(str)
    executed = QtCore.pyqtSignal(Shortcut)

    def __init__(self, filename: Path, tracking_file: Path):
        super().__init__()

        Shortcuts.instance = self

        self.execution_error.connect(lambda message: print(message))

        self.list: Dict[(str, str), Shortcut] = {}
        self.filename = filename
        self.tracking_file = tracking_file

    def add(self, shortcut: Shortcut):
        self.list[(shortcut.device, str(shortcut.key))] = shortcut

    def remove_by_device_key(self, device_name: str, key: ShortcutKey):
        self.list.pop((device_name, str(key)), None)

    def get_by_device_key(self, device_name: str, key: ShortcutKey):
        return self.list.get((device_name, str(key)))

    def get_list(self):
        return self.list

    def get_shortcuts(self):
        return self.list.values()

    def clear(self):
        self.list.clear()

    def load(self):
        if not self.filename.is_file():
            return

        with self.filename.open("r") as file:
            data = yaml.safe_load(file)

        tracking_data = {}
        try:
            with self.tracking_file.open("r") as tracking_file:
                tracking_data = yaml.safe_load(tracking_file)
        except FileNotFoundError:
            pass

        self.clear()

        for shortcut_data in data:
            shortcut = Shortcut.new_from_config(shortcut_data)
            shortcut.add_tracking_data(tracking_data.get(shortcut.uuid, {}))

            self.add(shortcut)

    def load_legacy(self, filename: Path, device):
        if not filename.is_file():
            return

        settings = QtCore.QSettings(str(filename), QtCore.QSettings.IniFormat)

        for section in settings.childGroups():
            settings.beginGroup(section)
            shortcut = Shortcut()
            shortcut.device = device
            shortcut.key = ShortcutKey.from_string(section)
            shortcut.name = settings.value("name")
            shortcut.action = settings.value("action")
            shortcut.data = settings.value("data")
            settings.endGroup()
            self.add(shortcut)

    def save(self):
        shortcuts = []
        tracking_data = {}

        for shortcut in sorted(self.get_shortcuts(), key=lambda shortcut_item: shortcut_item.name):
            shortcuts.append(shortcut.to_config())
            tracking_data[shortcut.uuid] = shortcut.to_tracking_data()

        temp_file = Path("{}.tmp".format(self.filename))

        # Write to a temporary file first to prevent data loss in case of a crash while saving
        with temp_file.open("w") as file:
            yaml.dump(shortcuts, file, default_flow_style=False)

        temp_file.rename(self.filename)

        temp_file = Path("{}.tmp".format(self.tracking_file))

        with temp_file.open("w") as file:
            yaml.dump(tracking_data, file, default_flow_style=False)

        temp_file.rename(self.tracking_file)


class ShortcutLabelPrinter(QtPrintSupport.QPrinter):
    def __init__(self, shortcuts: list[Shortcut]):
        super().__init__(QtPrintSupport.QPrinter.HighResolution)

        self.shortcuts = shortcuts

    def print_with_preview(self):
        print_dialog = QtPrintSupport.QPrintPreviewDialog(self)
        print_dialog.paintRequested.connect(self.print)
        print_dialog.exec_()

    def print(self):
        dpi_x = self.logicalDpiX()
        dpi_y = self.logicalDpiY()

        painter = QtGui.QPainter()
        painter.begin(self)

        shortcuts = sorted(self.shortcuts, key=lambda shortcut_item: "{}-{}".format(QtGui.QColor(shortcut_item.label.background_color).rgb() if shortcut_item.label.background_color else 0, shortcut_item.name))

        x = 0
        y = 0
        max_end_y = 0

        for shortcut in shortcuts:
            icon_path = shortcut.label.icon_path
            if not icon_path:
                continue

            label_width = LengthUnit.length_to_pixel(Config.labels_length_unit, shortcut.label.width or Config.default_label_width, dpi_x)
            label_height = LengthUnit.length_to_pixel(Config.labels_length_unit, shortcut.label.height or Config.default_label_height, dpi_y)
            icon_margin_x = LengthUnit.length_to_pixel(Config.labels_length_unit, Config.label_icon_margin, dpi_x)
            icon_margin_y = LengthUnit.length_to_pixel(Config.labels_length_unit, Config.label_icon_margin, dpi_y)

            end_x = x + label_width
            end_y = y + label_height
            max_end_y = max(max_end_y, end_y)

            if end_x > self.width():
                x = 0
                y = max_end_y
                end_x = x + label_width
                end_y = y + label_height

            if end_y > self.height():
                self.newPage()
                x = 0
                y = 0
                end_x = x + label_width
                end_y = y + label_height
                max_end_y = end_y

            icon = QtGui.QImage(icon_path)
            scaled_icon: QtGui.QImage = icon.scaled(label_width - icon_margin_x, label_height - icon_margin_y, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            if shortcut.label.background_color:
                painter.fillRect(x, y, label_width, label_height, QtGui.QColor(shortcut.label.background_color))

            icon_width = scaled_icon.width()
            icon_height = scaled_icon.height()

            painter.drawImage(int(x + (label_width - icon_width) / 2), int(y + (label_height - icon_height) / 2), scaled_icon)
            painter.setPen(QtGui.QColor("black"))
            painter.drawRect(x, y, label_width, label_height)

            x = end_x
