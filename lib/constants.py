import os

APP_NAME = "Keyboard Mapper"
APP_DESCRIPTION = "A tool for Linux desktops to map keys of dedicated keyboards to specific actions."
APP_COPYRIGHT = "© 2018-2021 Michael Wieland"
APP_WEBSITE = "https://gitlab.com/Programie/KeyboardMapper"
APP_VERSION = "3.0"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEVICES_BASE_DIR = "/dev/input/by-id"

try:
    from lib import resources

    ICONS_DIR = ":/icons"
    TRANSLATIONS_DIR = ":/translations"
except ImportError:
    ICONS_DIR = os.path.join(BASE_DIR, "icons")
    TRANSLATIONS_DIR = os.path.join(BASE_DIR, "translations")
