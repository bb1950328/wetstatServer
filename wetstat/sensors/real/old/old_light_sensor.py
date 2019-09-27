# coding=utf-8
from wetstat.sensors.abstract.base_sensor import BaseSensor


# noinspection PyMissingConstructor
class OldLightSensor(BaseSensor):

    def __init__(self):
        pass

    def get_long_name(self):
        return "Licht (Alt)"

    def get_short_name(self):
        return "OldLight"

    def get_display_color(self):
        return "#f9d607"

    def get_unit(self):
        return "V"

    def measure(self):
        raise NotImplementedError("Can't measure on deprecated sensors!!!")
