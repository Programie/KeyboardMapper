from pathlib import Path

APP_NAME = "Keyboard Mapper"
APP_DESCRIPTION = "A tool for Linux desktops to map keys of dedicated keyboards to specific actions."
APP_COPYRIGHT = "© 2018-2023 Michael Wieland"
APP_WEBSITE = "https://gitlab.com/Programie/KeyboardMapper"
APP_VERSION = "3.3"
BASE_DIR = Path(__file__).parent.parent
DEVICES_BASE_DIR = Path("/dev/input/by-id")

try:
    from lib import resources

    ICONS_DIR = Path(":/icons")
    TRANSLATIONS_DIR = Path(":/translations")
except ImportError:
    ICONS_DIR = BASE_DIR.joinpath("icons")
    TRANSLATIONS_DIR = BASE_DIR.joinpath("translations")
