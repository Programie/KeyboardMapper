#! /usr/bin/env python3
import enum
import os
import struct
import subprocess
import sys
import time
from select import select
from threading import Thread
from typing import List, Dict

import pyperclip as pyperclip
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QApplication

from xtestwrapper import XTestWrapper

APP_NAME = "Keyboard Mapper"
APP_DESCRIPTION = "A tool for Linux desktops to map keys of a dedicated keyboard to specific actions"
APP_WEBSITE = "https://gitlab.com/Programie/KeyboardMapper"
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class Config:
    filename = None
    keyboard_input_device = None
    icons = "dark"
    use_tray_icon = True

    @staticmethod
    def load():
        settings = QtCore.QSettings(Config.filename, QtCore.QSettings.IniFormat)

        Config.keyboard_input_device = settings.value("keyboard-input-device")
        Config.icons = settings.value("icons")
        Config.use_tray_icon = Config.to_boolean(str(settings.value("use-tray-icon")))

    @staticmethod
    def to_boolean(string: str):
        return string.lower() in ["1", "yes", "true", "on"]

    @staticmethod
    def save():
        settings = QtCore.QSettings(Config.filename, QtCore.QSettings.IniFormat)

        settings.setValue("keyboard-input-device", Config.keyboard_input_device)
        settings.setValue("icons", Config.icons)
        settings.setValue("use-tray-icon", Config.use_tray_icon)


class MainWindow(QtWidgets.QMainWindow):
    class ShortcutListHeader(enum.Enum):
        NAME, ACTION, KEY = range(3)

    instance: "MainWindow" = None

    def __init__(self, shortcuts: "Shortcuts"):
        super().__init__()

        # Required by other classes which don't know this instance
        MainWindow.instance = self

        self.shortcuts = shortcuts

        self.setWindowTitle("Keyboard Mapper")

        menu_bar = QtWidgets.QMenuBar()

        file_menu = QtWidgets.QMenu("File")
        file_menu.addAction("Settings...", self.show_settings)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.quit)

        edit_menu = QtWidgets.QMenu("Edit")
        edit_menu.addAction("Add shortcut...", self.add_shortcut)
        edit_menu.addAction("Edit shortcut...", self.edit_shortcut)
        edit_menu.addAction("Remove shortcut", self.remove_shortcut)

        help_menu = QtWidgets.QMenu("Help")
        help_menu.addAction("Help", self.show_help).setShortcut(QtGui.QKeySequence("F1"))
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

        self.shortcut_tree_view = QtWidgets.QTreeView()
        self.shortcut_tree_view.setAlternatingRowColors(True)
        self.shortcut_tree_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.shortcut_tree_view_model = QtGui.QStandardItemModel(0, 3)
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.NAME.value, QtCore.Qt.Horizontal, "Name")
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.ACTION.value, QtCore.Qt.Horizontal, "Action")
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.KEY.value, QtCore.Qt.Horizontal, "Key")
        self.shortcut_tree_view.setModel(self.shortcut_tree_view_model)

        self.shortcut_tree_view.doubleClicked.connect(lambda model_index: self.edit_item(model_index.siblingAtColumn(self.ShortcutListHeader.KEY.value).data()))

        self.setCentralWidget(self.shortcut_tree_view)

        self.tray_icon: QtWidgets.QSystemTrayIcon = None
        self.update_tray_icon()

        self.load_from_shortcuts()

    def update_tray_icon(self):
        if Config.use_tray_icon and QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            tray_menu = QtWidgets.QMenu()

            tray_menu.addAction("Show window", self.show)
            tray_menu.addSeparator()
            tray_menu.addAction("Quit", self.quit)

            icon_name = ["appicon", Config.icons]

            if KeyListener.allowed_actions == AllowedActions.LOCK_KEYS:
                icon_name.append("disabled")

            self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon("icons/{}.png".format("-".join(icon_name))))
            self.tray_icon.show()
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.handle_tray_icon_activation)
        else:
            self.tray_icon = None

    def add_list_item(self, shortcut: "Shortcut"):
        model = self.shortcut_tree_view_model

        model.insertRow(0)
        model.setData(model.index(0, self.ShortcutListHeader.NAME.value), shortcut.name)
        model.setData(model.index(0, self.ShortcutListHeader.ACTION.value), shortcut.get_action_name())
        model.setData(model.index(0, self.ShortcutListHeader.KEY.value), shortcut.key)

    def load_from_shortcuts(self):
        self.shortcut_tree_view_model.removeRows(0, self.shortcut_tree_view_model.rowCount())

        for shortcut in self.shortcuts.get_list().values():
            self.add_list_item(shortcut)

    def edit_item(self, key=None):
        if key is None:
            shortcut = None
        else:
            shortcut = self.shortcuts.get_by_key(key)

        EditShortcutWindow(self, shortcut)

    def show_settings(self):
        SettingsWindow(self)

    def quit(self):
        sys.exit()

    def add_shortcut(self):
        self.edit_item(None)

    def edit_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        self.edit_item(selected_indexes[0].siblingAtColumn(self.ShortcutListHeader.KEY.value).data())

    def remove_shortcut(self):
        pass

    def show_help(self):
        subprocess.run(["xdg-open", APP_WEBSITE])

    def show_about(self):
        QtWidgets.QMessageBox.aboutQt(self, "About")

    def handle_tray_icon_activation(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def closeEvent(self, event: QtGui.QCloseEvent):
        # Only hide if the tray icon is available
        if self.tray_icon:
            self.hide()
            event.ignore()


class EditShortcutWindow(QtWidgets.QDialog):
    def __init__(self, parent: MainWindow, shortcut: "Shortcut"):
        super().__init__(parent)

        self.shortcut = shortcut

        if shortcut:
            self.setWindowTitle("Edit shortcut")
        else:
            self.setWindowTitle("Add shortcut")

        self.setModal(True)

        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.shortcut_button = None
        self.add_shortcut_button()

        self.name_field = None
        self.add_name_field()

        self.action_options: List[QtWidgets.QRadioButton] = []
        self.action_launch_application_list = None
        self.execute_command_field = None
        self.open_folder_field = None
        self.input_text_field = None
        self.input_key_sequence_field = None
        self.add_action_options()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()

    def add_shortcut_button(self):
        group_box = QtWidgets.QGroupBox("Shortcut")
        self.dialog_layout.addWidget(group_box)

        if self.shortcut:
            text = str(self.shortcut.key)
        else:
            text = "Click to set shortcut"

        self.shortcut_button = QtWidgets.QPushButton(text)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.shortcut_button)
        group_box.setLayout(layout)

    def add_name_field(self):
        group_box = QtWidgets.QGroupBox("Name")
        self.dialog_layout.addWidget(group_box)

        if self.shortcut:
            text = self.shortcut.name
        else:
            text = ""

        self.name_field = QtWidgets.QLineEdit(text)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.name_field)
        group_box.setLayout(layout)

    def add_action_options(self):
        group_box = QtWidgets.QGroupBox("Action")
        self.dialog_layout.addWidget(group_box)

        layout = QtWidgets.QGridLayout()
        group_box.setLayout(layout)

        self.action_launch_application_list = QtWidgets.QComboBox()
        self.execute_command_field = QtWidgets.QLineEdit()
        self.open_folder_field = QtWidgets.QLineEdit()
        self.input_text_field = QtWidgets.QLineEdit()
        self.input_key_sequence_field = QtWidgets.QLineEdit()

        select_folder_button = QtWidgets.QPushButton("Browse...")
        select_folder_button.clicked.connect(self.select_folder)

        self.action_options = [
            [None, Actions.LAUNCH_APPLICATION, [self.action_launch_application_list]],
            [None, Actions.EXECUTE_COMMAND, [self.execute_command_field]],
            [None, Actions.OPEN_FOLDER, [self.open_folder_field, select_folder_button]],
            [None, Actions.INPUT_TEXT, [self.input_text_field]],
            [None, Actions.INPUT_KEY_SEQUENCE, [self.input_key_sequence_field]],
            [None, Actions.LOCK_KEYS, []]
        ]

        for row, action in enumerate(self.action_options):
            radio_button, action, fields = action

            radio_button = QtWidgets.QRadioButton(action.title)
            radio_button.clicked.connect(self.update_action_states)
            self.action_options[row][0] = radio_button
            layout.addWidget(radio_button, row, 0)

            for column, field in enumerate(fields, start=1):
                layout.addWidget(field, row, column)

            if self.shortcut and self.shortcut.action == action.name:
                radio_button.setChecked(True)

                if action == Actions.LAUNCH_APPLICATION:
                    # TODO: self.action_launch_application_list.setCurrentIndex()
                    pass
                elif action == Actions.EXECUTE_COMMAND:
                    self.execute_command_field.setText(self.shortcut.data)
                elif action == Actions.OPEN_FOLDER:
                    self.open_folder_field.setText(self.shortcut.data)
                elif action == Actions.INPUT_TEXT:
                    self.input_text_field.setText(self.shortcut.data)
                elif action == Actions.INPUT_KEY_SEQUENCE:
                    self.input_key_sequence_field.setText(self.shortcut.data)

        self.update_action_states()

    def update_action_states(self):
        for action in self.action_options:
            radio_button, action, fields = action

            enabled = radio_button.isChecked()

            for field in fields:
                field.setEnabled(enabled)

    def select_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder to open", self.open_folder_field.text(), QtWidgets.QFileDialog.DontUseNativeDialog | QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)

        if path:
            self.open_folder_field.setText(path)

    def save(self):
        pass


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)

        self.main_window = parent

        self.setWindowTitle("Settings")
        self.setModal(True)

        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.input_device_list: QtWidgets.QListWidget = None
        self.add_keyboard_input_device_settings()

        self.icon_theme_list: QtWidgets.QComboBox = None
        self.add_icon_theme_settings()

        self.use_tray_icon_checkbox = QtWidgets.QCheckBox("Enable tray icon")
        self.use_tray_icon_checkbox.setEnabled(QtWidgets.QSystemTrayIcon.isSystemTrayAvailable())
        self.use_tray_icon_checkbox.setChecked(Config.use_tray_icon)
        self.dialog_layout.addWidget(self.use_tray_icon_checkbox)

        create_desktop_file_button = QtWidgets.QPushButton("Create desktop file")
        create_desktop_file_button.clicked.connect(self.create_desktop_file)
        self.dialog_layout.addWidget(create_desktop_file_button)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()

    def add_keyboard_input_device_settings(self):
        group_box = QtWidgets.QGroupBox("Keyboard input device")
        self.dialog_layout.addWidget(group_box)

        self.input_device_list = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.input_device_list)
        group_box.setLayout(layout)

        if Config.keyboard_input_device is None:
            active_device_file = None
        else:
            active_device_file = QtCore.QFileInfo(Config.keyboard_input_device)

        file_list: List[QtCore.QFileInfo] = QtCore.QDir("/dev/input/by-id").entryInfoList()
        for item in file_list:
            if item.isDir():
                continue

            name = item.baseName()

            list_item = QtWidgets.QListWidgetItem(name)
            self.input_device_list.addItem(list_item)

            if active_device_file and active_device_file.baseName() == name:
                self.input_device_list.setCurrentItem(list_item)

    def add_icon_theme_settings(self):
        group_box = QtWidgets.QGroupBox("Icon theme")
        self.dialog_layout.addWidget(group_box)

        self.icon_theme_list = QtWidgets.QComboBox()
        self.icon_theme_list.addItem("bright")
        self.icon_theme_list.addItem("dark")

        self.icon_theme_list.setCurrentText(Config.icons)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.icon_theme_list)
        group_box.setLayout(layout)

    def create_desktop_file(self):
        with open(os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "keyboard-mapper.desktop"), "w") as file:
            lines = [
                "[Desktop Entry]",
                "Comment={}".format(APP_DESCRIPTION),
                "Name={}".format(APP_NAME),
                "Type=Application",
                "Categories=System;",
                "Exec={}".format(sys.argv[0]),
                "Icon={}".format(os.path.join(BASE_DIR, "icons", "appicon-{}.png".format(Config.icons)))
            ]

            file.write("\n".join(lines))

    def save(self):
        input_device_items: List[QtWidgets.QListWidgetItem] = self.input_device_list.selectedItems()

        if len(input_device_items) == 0:
            QtWidgets.QMessageBox.critical(self, "No keyboard input device selected", "Please selected the input device to use!")

        Config.keyboard_input_device = "/dev/input/by-id/{}".format(input_device_items[0].text())
        Config.icons = self.icon_theme_list.currentText()
        Config.use_tray_icon = self.use_tray_icon_checkbox.checkState() == QtCore.Qt.Checked

        Config.save()

        self.main_window.update_tray_icon()
        KeyListener.reload = True

        self.close()


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
            # TODO: Launch application
            pass
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
            if KeyListener.allowed_actions == AllowedActions.ALL:
                KeyListener.allowed_actions = AllowedActions.LOCK_KEYS
            elif KeyListener.allowed_actions == AllowedActions.LOCK_KEYS:
                KeyListener.allowed_actions = AllowedActions.ALL

            if MainWindow.instance and MainWindow.instance.tray_icon:
                MainWindow.instance.update_tray_icon()


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
        settings = QtCore.QSettings(self.filename, QtCore.QSettings.IniFormat)

        self.clear()

        for section in settings.childGroups():
            settings.beginGroup(section)
            self.add(Shortcut.new_from_config(section, settings))
            settings.endGroup()

    def save(self):
        settings = QtCore.QSettings(self.filename, QtCore.QSettings.IniFormat)

        for shortcut in self.list:
            settings.beginGroup(str(shortcut.key))
            shortcut.to_config(settings)
            settings.endGroup()


class AllowedActions(enum.Enum):
    NONE = 0
    LOCK_KEYS = 1
    ALL = 2


class KeyListener(Thread):
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    reload = False
    allowed_actions = AllowedActions.ALL

    def __init__(self, shortcuts: Shortcuts):
        super().__init__()

        self.shortcuts = shortcuts

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
                        if KeyListener.reload:
                            KeyListener.reload = False
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
            except:
                pass

            time.sleep(1)

    def handle_key_press(self, key_code):
        print(key_code)

        # Skip if disabled
        if KeyListener.allowed_actions == AllowedActions.NONE:
            return

        # Skip if shortcut not configured
        shortcut: Shortcut = self.shortcuts.get_by_key(key_code)
        if shortcut is None:
            return

        # Skip if keys are locked and this shortcut is not used to lock/unlock keys
        if KeyListener.allowed_actions == AllowedActions.LOCK_KEYS and shortcut.action != Actions.LOCK_KEYS.name:
            return

        shortcut.execute()


def main():
    application = QApplication(sys.argv)

    config_dir = os.path.join(os.path.expanduser("~"), ".config", "keyboard-mapper")

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    Config.filename = os.path.join(config_dir, "config.ini")
    Config.load()

    shortcuts = Shortcuts(os.path.join(config_dir, "shortcuts.ini"))
    shortcuts.load()

    key_listener = KeyListener(shortcuts)
    key_listener.setDaemon(True)
    key_listener.start()

    main_window = MainWindow(shortcuts)
    main_window.show()

    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
