from wetstat.sensors.BaseSensor import BaseSensor


class TempSensor(BaseSensor):

    def __init__(self, number):
        self.number = number
        self.adc = None

    def get_long_name(self):
        return "Temperatur " + self.number

    def get_short_name(self):
        return "Temp" + self.number

    def get_display_color(self):
        n = str(hex(self.number + 210))
        if len(n) == 1:
            n = "0" + n
        return "#3875" + n

    def set_adc(self, adc):
        self.adc = adc

    def measure(self):
        # TODO
        pass
