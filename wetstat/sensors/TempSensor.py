# coding=utf-8
from wetstat.sensors.AnalogDigitalConverter import AnalogDigitalConverter
from wetstat.sensors.BaseSensor import BaseSensor


class TempSensor(BaseSensor):

    # noinspection PyMissingConstructor
    def __init__(self, number):
        self.number = number
        self.adc = None

    def get_long_name(self):
        return f"Temperatur {self.number}"

    def get_short_name(self):
        return f"Temp{self.number}"

    def get_display_color(self):
        blue = (self.number * 50 + 150) % 255
        n = str(hex(blue))
        n = n[2:]
        if len(n) == 1:
            n = "0" + n
        return f"#3875{n}"

    def get_unit(self):
        return "°C"

    def set_adc(self, adc):
        self.adc = adc

    def get_adc(self):
        if self.adc is None:
            self.adc = AnalogDigitalConverter()
        return self.adc

    def measure(self):
        volt = self.get_adc().read_channel(max(7, min(0, self.number - 1)))  # limit channel
        return 35.744 * volt - 37.451
