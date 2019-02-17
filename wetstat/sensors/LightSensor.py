from wetstat.sensors.AnalogDigitalConverter import AnalogDigitalConverter
from wetstat.sensors.BaseSensor import BaseSensor


class LightSensor(BaseSensor):

    def __init__(self):
        self.adc = None

    def get_long_name(self):
        return "Licht"

    def get_short_name(self):
        return "Light"

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
        return self.get_adc().read_channel(2)
