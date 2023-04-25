import os
from typing import List

from PyQt5.QtCore import QSettings


class Config:
    filename: str = None
    input_devices: List[str] = []
    icons: str = "dark"
    use_tray_icon: bool = True
    single_instance: bool = True
    list_sort_column: str = None
    list_sort_order: str = None
    labels_length_unit: str = None
    default_label_width: int = None
    default_label_height: int = None
    label_icon_margin: int = None

    @staticmethod
    def load():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        legacy_device = os.path.basename(str(settings.value("keyboard-input-device"))).strip()
        Config.input_devices = list(set(filter(None, str(settings.value("input-devices", defaultValue=legacy_device)).split(","))))
        Config.icons = settings.value("icons", defaultValue="dark")
        Config.use_tray_icon = Config.to_boolean(str(settings.value("use-tray-icon", defaultValue=True)))
        Config.single_instance = Config.to_boolean(str(settings.value("single-instance", defaultValue=True)))

        settings.beginGroup("List")
        Config.list_sort_column = settings.value("sort-column", defaultValue="name")
        Config.list_sort_order = settings.value("sort-order", defaultValue="asc")
        settings.endGroup()

        settings.beginGroup("Labels")
        Config.labels_length_unit = settings.value("length-unit", defaultValue="mm")
        Config.default_label_width = Config.to_integer(settings.value("default-width", defaultValue=None))
        Config.default_label_height = Config.to_integer(settings.value("default-height", defaultValue=None))
        Config.label_icon_margin = Config.to_integer(settings.value("icon-margin", defaultValue=1))
        settings.endGroup()

        if legacy_device != "":
            settings.remove("keyboard-input-device")
            Config.save()

    @staticmethod
    def to_boolean(string: str):
        return string.lower() in ["1", "yes", "true", "on"]

    @staticmethod
    def to_integer(string: str):
        if string is None:
            return None

        return int(string)

    @staticmethod
    def save():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        settings.setValue("input-devices", ",".join(sorted(Config.input_devices)))
        settings.setValue("icons", Config.icons)
        settings.setValue("use-tray-icon", Config.use_tray_icon)
        settings.setValue("single-instance", Config.single_instance)

        settings.beginGroup("List")
        settings.setValue("sort-column", Config.list_sort_column)
        settings.setValue("sort-order", Config.list_sort_order)
        settings.endGroup()

        settings.beginGroup("Labels")
        settings.setValue("length-unit", Config.labels_length_unit)
        settings.setValue("default-width", Config.default_label_width)
        settings.setValue("default-height", Config.default_label_height)
        settings.setValue("icon-margin", Config.label_icon_margin)
        settings.endGroup()
