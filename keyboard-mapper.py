#! /usr/bin/env python3
import os
import sys
import time

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QApplication
from filelock import FileLock, Timeout

from lib.config import Config
from lib.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION, DEVICES_BASE_DIR, ICONS_DIR, TRANSLATIONS_DIR
from lib.gui import MainWindow
from lib.keylistener_manager import KeyListenerManager
from lib.shortcut import Shortcuts


def main():
    if "--no-gui" in sys.argv:
        application = QCoreApplication(sys.argv)
        gui_mode = False
    else:
        application = QApplication(sys.argv)
        gui_mode = True

    application.setApplicationName(APP_NAME)
    application.setApplicationVersion(APP_VERSION)

    parser = QtCore.QCommandLineParser()
    parser.setApplicationDescription(APP_DESCRIPTION)
    parser.addHelpOption()
    parser.addVersionOption()

    config_dir = os.path.join(os.path.expanduser("~"), ".config", "keyboard-mapper")

    config_dir_option = QtCore.QCommandLineOption(["c", "config-dir"], "Path to the config dir (default: {})".format(config_dir), defaultValue=config_dir)
    parser.addOption(config_dir_option)

    hidden_option = QtCore.QCommandLineOption(["H", "hidden"], "Start hidden")
    parser.addOption(hidden_option)

    parser.addOption(QtCore.QCommandLineOption(["no-gui"], "Start without GUI"))

    parser.process(application)

    config_dir = parser.value(config_dir_option)

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    Config.filename = os.path.join(config_dir, "config.ini")
    Config.load()

    if gui_mode:
        application.setWindowIcon(QtGui.QIcon(os.path.join(ICONS_DIR, "appicon-{}.png".format(Config.icons))))

    if Config.single_instance:
        user_run_dir = os.path.join("var", "run", "user", str(os.getuid()))
        if os.path.exists(user_run_dir):
            lock_file = os.path.join(user_run_dir, "keyboard-mapper.lock")
        else:
            lock_file = os.path.join(config_dir, "app.lock")

        lock = FileLock(lock_file, timeout=1)

        try:
            lock.acquire()
        except Timeout:
            message = "Keyboard Mapper is already running!"
            if gui_mode:
                QtWidgets.QMessageBox.critical(None, APP_NAME, message)
            else:
                print(message)
            sys.exit(1)

    translator = QtCore.QTranslator(application)
    translator.load(QtCore.QLocale().name(), directory=TRANSLATIONS_DIR)
    application.installTranslator(translator)

    shortcuts_file = os.path.join(config_dir, "shortcuts.yaml")
    legacy_shortcuts_file = os.path.join(config_dir, "shortcuts.ini")

    shortcuts = Shortcuts(shortcuts_file)

    if os.path.exists(legacy_shortcuts_file) and not os.path.exists(shortcuts_file):
        if len(Config.input_devices):
            shortcuts.load_legacy(legacy_shortcuts_file, Config.input_devices[0])

    shortcuts.load()

    key_listener_manager = KeyListenerManager(DEVICES_BASE_DIR, shortcuts)
    key_listener_manager.set_device_files(Config.input_devices)

    if gui_mode:
        main_window = MainWindow(shortcuts, key_listener_manager)

        if not parser.isSet(hidden_option):
            main_window.show()

        sys.exit(application.exec_())
    else:
        print("Listening for keyboard events")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        key_listener_manager.stop_threads()


if __name__ == "__main__":
    main()
