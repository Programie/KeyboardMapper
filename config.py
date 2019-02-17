from PySide2.QtCore import QSettings


class Config:
    DEFAULT_SECTION = "options"

    filename = None
    keyboard_input_device = None
    icons = "dark"
    use_tray_icon = True

    @staticmethod
    def load():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        Config.keyboard_input_device = settings.value("keyboard-input-device")
        Config.icons = settings.value("icons")
        Config.use_tray_icon = Config.to_boolean(str(settings.value("use-tray-icon")))

    @staticmethod
    def to_boolean(string: str):
        return string.lower() in ["1", "yes", "true", "on"]

    @staticmethod
    def save():
        settings = QSettings(Config.filename, QSettings.IniFormat)

        settings.setValue("keyboard-input-device", Config.keyboard_input_device)
        settings.setValue("icons", Config.icons)
        settings.setValue("use-tray-icon", Config.use_tray_icon)
