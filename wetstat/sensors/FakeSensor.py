import random

from wetstat.sensors.BaseSensor import BaseSensor


class FakeSensor(BaseSensor):

    def __init__(self, number):
        self.number = number
        self.last = random.randint(-500, 500) / 10

    def get_long_name(self):
        return f"FakeSensor {self.number}"

    def get_short_name(self):
        return f"Fake{self.number}"

    def get_display_color(self):
        n = str(hex(self.number + 210))
        if len(n) == 1:
            n = "0" + n
        return f"#0075{n}"

    def get_unit(self):
        return "Fakes"

    def measure(self):
        new = self.last + (random.randint(-50, 50) / 10)  # +/- 5
        self.last = new
        return new
