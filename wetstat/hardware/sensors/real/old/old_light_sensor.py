# coding=utf-8
from wetstat.hardware.sensors.abstract.analog_digital_converter import AnalogDigitalConverter
from wetstat.hardware.sensors.abstract.base_sensor import BaseSensor


# noinspection PyMissingConstructor
class OldLightSensor(BaseSensor):

    def __init__(self):
        self.adc = None

    def get_long_name(self):
        return "Licht (Alt)"

    def get_short_name(self):
        return "OldLight"

    def get_display_color(self):
        return "#f9d607"

    def get_unit(self):
        return "V"

    def set_adc(self, adc):
        self.adc = adc

    def get_adc(self):
        if self.adc is None:
            self.adc = AnalogDigitalConverter()
        return self.adc

    def measure(self):
        raise NotImplementedError("Can't measure on deprecated sensors!!!")
