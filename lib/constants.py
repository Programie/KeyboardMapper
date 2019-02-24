import os

APP_NAME = "Keyboard Mapper"
APP_DESCRIPTION = "A tool for Linux desktops to map keys of dedicated keyboards to specific actions."
APP_COPYRIGHT = "© 2018-2019 Michael Wieland"
APP_WEBSITE = "https://gitlab.com/Programie/KeyboardMapper"
APP_VERSION = "1.0"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
DEVICES_BASE_DIR = "/dev/input/by-id"
