#! /usr/bin/env python3
import os
from pathlib import Path

import sys
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication
from filelock import FileLock, Timeout

from lib.config import Config
from lib.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION, DEVICES_BASE_DIR, ICONS_DIR, TRANSLATIONS_DIR
from lib.gui import MainWindow
from lib.keylistener_manager import KeyListenerManager
from lib.shortcut import Shortcuts

translate = QtWidgets.QApplication.translate


def main():
    if "--no-gui" in sys.argv:
        application = QCoreApplication(sys.argv)
        gui_mode = False
    else:
        application = QApplication(sys.argv)
        application.setQuitOnLastWindowClosed(False)
        gui_mode = True

    application.setApplicationName(APP_NAME)
    application.setApplicationVersion(APP_VERSION)

    translator = QtCore.QTranslator(application)
    translator.load(QtCore.QLocale().name(), directory=str(TRANSLATIONS_DIR))
    application.installTranslator(translator)

    parser = QtCore.QCommandLineParser()
    parser.setApplicationDescription(APP_DESCRIPTION)
    parser.addHelpOption()
    parser.addVersionOption()

    config_dir = Path("~/.config/keyboard-mapper").expanduser()

    config_dir_option = QtCore.QCommandLineOption(["c", "config-dir"], "Path to the config dir (default: {})".format(str(config_dir)), defaultValue=str(config_dir))
    parser.addOption(config_dir_option)

    hidden_option = QtCore.QCommandLineOption(["H", "hidden"], "Start hidden")
    parser.addOption(hidden_option)

    parser.addOption(QtCore.QCommandLineOption(["no-gui"], "Start without GUI"))

    parser.process(application)

    config_dir = Path(parser.value(config_dir_option))

    if not config_dir.is_dir():
        config_dir.mkdir()

    Config.filename = config_dir.joinpath("config.ini")
    Config.load()

    if gui_mode:
        application.setWindowIcon(QtGui.QIcon(str(ICONS_DIR.joinpath("appicon-{}.png".format(Config.icons)))))

    if Config.single_instance:
        user_run_dir = Path("/var/run/user").joinpath(str(os.getuid()))
        if user_run_dir.is_dir():
            lock_file = user_run_dir.joinpath("keyboard-mapper.lock")
        else:
            lock_file = config_dir.joinpath("app.lock")

        lock = FileLock(lock_file, timeout=1)

        try:
            lock.acquire()
        except Timeout:
            message = translate("main", "Keyboard Mapper is already running!")
            if gui_mode:
                QtWidgets.QMessageBox.critical(None, APP_NAME, message)
            else:
                print(message)
            sys.exit(1)

    shortcuts_file = config_dir.joinpath("shortcuts.yaml")
    tracking_file = config_dir.joinpath("tracking.yaml")
    legacy_shortcuts_file = config_dir.joinpath("shortcuts.ini")

    shortcuts = Shortcuts(shortcuts_file, tracking_file)

    if legacy_shortcuts_file.is_file() and not shortcuts_file.is_file():
        if len(Config.input_devices):
            shortcuts.load_legacy(legacy_shortcuts_file, Config.input_devices[0])

    try:
        shortcuts.load()
    except Exception as exception:
        message = translate("main", "Unable to load shortcuts from config file!") + "\n\n" + str(exception)
        if gui_mode:
            if QtWidgets.QMessageBox.critical(None, APP_NAME, message, QtWidgets.QMessageBox.Close, QtWidgets.QMessageBox.Ignore) == QtWidgets.QMessageBox.Close:
                sys.exit(1)
        else:
            print(message)
            sys.exit(1)

    key_listener_manager = KeyListenerManager(DEVICES_BASE_DIR, shortcuts)
    key_listener_manager.set_device_files(Config.input_devices)

    if gui_mode:
        main_window = MainWindow(shortcuts, key_listener_manager)

        if not parser.isSet(hidden_option):
            main_window.show()

        try:
            exit_code = application.exec_()
        finally:
            shortcuts.save()

        sys.exit(exit_code)
    else:
        print("Listening for keyboard events")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        key_listener_manager.stop_threads()
        shortcuts.save()


if __name__ == "__main__":
    main()
