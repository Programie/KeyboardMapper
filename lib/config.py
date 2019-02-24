import os
from typing import List

from PySide2.QtCore import QSettings


class Config:
    filename: str = None
    input_devices: List[str] = []
    icons: str = "dark"
    use_tray_icon: bool = True
    single_instance: bool = True

    @staticmethod
    def load():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        legacy_device = os.path.basename(str(settings.value("keyboard-input-device"))).strip()
        Config.input_devices = list(set(filter(None, str(settings.value("input-devices", defaultValue=legacy_device)).split(","))))
        Config.icons = settings.value("icons", defaultValue="dark")
        Config.use_tray_icon = Config.to_boolean(str(settings.value("use-tray-icon", defaultValue=True)))
        Config.single_instance = Config.to_boolean(str(settings.value("single-instance", defaultValue=True)))

        if legacy_device != "":
            settings.remove("keyboard-input-device")
            Config.save()

    @staticmethod
    def to_boolean(string: str):
        return string.lower() in ["1", "yes", "true", "on"]

    @staticmethod
    def save():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        settings.setValue("input-devices", ",".join(Config.input_devices))
        settings.setValue("icons", Config.icons)
        settings.setValue("use-tray-icon", Config.use_tray_icon)
        settings.setValue("single-instance", Config.single_instance)
