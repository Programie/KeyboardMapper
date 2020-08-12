from typing import Dict

from PySide2 import QtWidgets

translate = QtWidgets.QApplication.translate


class LengthUnit:
    UNIT_MM = "mm"
    UNIT_INCH = "inch"
    UNIT_PIXEL = "pixel"

    class Unit:
        title: str
        suffix: str

        def __init__(self, title, suffix):
            self.title = title
            self.suffix = suffix

    units: Dict[str, Unit] = {
        # title, internal name, suffix
        UNIT_MM: Unit(translate("settings", "Millimeter"), "mm"),
        UNIT_INCH: Unit(translate("settings", "Inch"), "\""),
        UNIT_PIXEL: Unit(translate("settings", "Pixel"), "px")
    }

    @staticmethod
    def length_to_pixel(unit, length, dpi):
        if unit == LengthUnit.UNIT_MM:
            return int(length / 25.4 * dpi)
        elif unit == LengthUnit.UNIT_INCH:
            return int(length * dpi)
        else:
            return int(length)
