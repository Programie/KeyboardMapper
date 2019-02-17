#! /usr/bin/env python3
import os
import sys
from PySide2.QtWidgets import QApplication

from config import Config
from shortcut import Shortcuts
from window import MainWindow


def main():
    application = QApplication(sys.argv)

    config_dir = os.path.join(os.path.expanduser("~"), ".config", "keyboard-mapper")

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    Config.filename = os.path.join(config_dir, "config.ini")
    Config.load()

    shortcuts = Shortcuts(os.path.join(config_dir, "shortcuts.ini"))
    shortcuts.load()

    main_window = MainWindow()
    main_window.load_from_shortcuts(shortcuts)
    main_window.show()

    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
