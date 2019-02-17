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

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QApplication


class Config:
    DEFAULT_SECTION = "options"

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

    def __init__(self):
        super().__init__()

        # Required by other classes which don't know this instance
        MainWindow.instance = self

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

        self.shortcut_tree_view.doubleClicked.connect(lambda model_index: self.edit_item(model_index.row()))

        self.setCentralWidget(self.shortcut_tree_view)

        self.tray_icon: QtWidgets.QSystemTrayIcon = None
        self.update_tray_icon()

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

    def load_from_shortcuts(self, shortcuts: "Shortcuts"):
        self.shortcut_tree_view_model.removeRows(0, self.shortcut_tree_view_model.rowCount())

        for shortcut in shortcuts.get_list().values():
            self.add_list_item(shortcut)

    def edit_item(self, row=None):
        print("Edit row {}".format(row))

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

        self.edit_item(selected_indexes[0].row())

    def remove_shortcut(self):
        pass

    def show_help(self):
        subprocess.run(["xdg-open", "https://gitlab.com/Programie/KeyboardMapper"])

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


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)

        self.main_window = parent

        self.setWindowTitle("Settings")

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
        self.key = None
        self.action = None
        self.data = None
        self.name = None

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
            # TODO: Execute command
            pass
        elif self.action == Actions.OPEN_FOLDER.name:
            # TODO: Open folder
            pass
        elif self.action == Actions.INPUT_TEXT.name:
            # TODO: Input text
            pass
        elif self.action == Actions.INPUT_KEY_SEQUENCE.name:
            # TODO: Input key sequence
            pass
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
            settings.beginGroup(shortcut.key)
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

    main_window = MainWindow()
    main_window.load_from_shortcuts(shortcuts)
    main_window.show()

    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
