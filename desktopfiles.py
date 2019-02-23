import os
from configparser import ConfigParser, SectionProxy
from typing import List


class DesktopFile:
    def __init__(self, filename: str):
        self.config_parser = ConfigParser()

        # Preserve case of property names (https://stackoverflow.com/a/1611877)
        self.config_parser.optionxform = str

        self.filename = filename
        self.name: str = None
        self.comment: str = None
        self.type: str = None
        self.exec: str = None
        self.path: str = None
        self.icon: str = None
        self.categories: List[str] = None
        self.no_display = False
        self.hidden = False
        self.only_show_in: List[str] = None
        self.not_show_in: List[str] = None

    @staticmethod
    def read(filename: str):
        desktop_file = DesktopFile(filename)

        desktop_file.config_parser.read(filename)
        section: SectionProxy = desktop_file.config_parser["Desktop Entry"]

        desktop_file.name = section.get("Name", raw=True)
        desktop_file.comment = section.get("Comment", raw=True)
        desktop_file.type = section.get("Type", raw=True, fallback="Application")
        desktop_file.exec = section.get("Exec", raw=True)
        desktop_file.path = section.get("Path", raw=True)
        desktop_file.icon = section.get("Icon", raw=True)
        desktop_file.categories = DesktopFile.string_to_list(section.get("Categories", raw=True))
        desktop_file.no_display = section.get("NoDisplay", raw=True, fallback=False, _impl=desktop_file.config_parser.getboolean)
        desktop_file.hidden = section.get("Hidden", raw=True, fallback=False, _impl=desktop_file.config_parser.getboolean)
        desktop_file.only_show_in = DesktopFile.string_to_list(section.get("OnlyShowIn", raw=True))
        desktop_file.not_show_in = DesktopFile.string_to_list(section.get("NotShowIn", raw=True))

        return desktop_file

    def write(self):
        if "Desktop Entry" not in self.config_parser:
            self.config_parser["Desktop Entry"] = {}

        properties = self.config_parser["Desktop Entry"]

        DesktopFile.add_dict(properties, "Name", self.name)
        DesktopFile.add_dict(properties, "Comment", self.comment)
        DesktopFile.add_dict(properties, "Type", self.type)
        DesktopFile.add_dict(properties, "Exec", self.exec)
        DesktopFile.add_dict(properties, "Path", self.path)
        DesktopFile.add_dict(properties, "Icon", self.icon)
        DesktopFile.add_dict(properties, "Categories", self.categories, self.list_to_string)
        DesktopFile.add_dict(properties, "NoDisplay", self.no_display, self.boolean_true_to_string)
        DesktopFile.add_dict(properties, "Hidden", self.hidden, self.boolean_true_to_string)
        DesktopFile.add_dict(properties, "OnlyShowIn", self.only_show_in, self.list_to_string)
        DesktopFile.add_dict(properties, "NotShowIn", self.not_show_in, self.list_to_string)

        with open(self.filename, "w") as file:
            self.config_parser.write(file)

    def is_visible(self):
        if self.type.lower() != "application":
            return False

        if self.no_display:
            return False

        if self.hidden:
            return False

        current_desktop = os.getenv("XDG_CURRENT_DESKTOP")

        if self.only_show_in and current_desktop not in self.only_show_in:
            return False

        if self.not_show_in and current_desktop in self.not_show_in:
            return False

        return True

    @staticmethod
    def string_to_list(string: str):
        if string is None:
            return None

        return list(filter(None, string.split(";")))

    @staticmethod
    def list_to_string(strings: List[str]):
        if strings is None:
            return None

        return ";".join(strings) + ";"

    @staticmethod
    def boolean_true_to_string(boolean: bool):
        if boolean:
            return "true"
        else:
            return None

    @staticmethod
    def add_dict(dictionary, key: str, value, converter: callable = None):
        if converter:
            value = converter(value)

        if value is None:
            if key in dictionary:
                del dictionary[key]
            return

        dictionary[key] = value


class DesktopFilesFinder:
    @staticmethod
    def load_in_known_paths():
        yield from DesktopFilesFinder.load_in_path("/usr/share/applications")
        yield from DesktopFilesFinder.load_in_path("/var/lib/snapd/desktop/applications")
        yield from DesktopFilesFinder.load_in_path(os.path.join(os.path.expanduser("~"), ".local", "share", "applications"))

    @staticmethod
    def load_in_path(path: str):
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1] != ".desktop":
                    continue

                yield DesktopFile.read(os.path.join(root, file))