# coding=utf-8
from wetstat.sensors.real.temp_sensor import TempSensor


class OldTempSensor(TempSensor):
    def __init__(self, number: int):
        super().__init__(number)

    def get_long_name(self) -> str:
        return super().get_long_name() + " (Alt)"

    def get_short_name(self) -> str:
        return "Old" + super().get_short_name()

    def measure(self) -> float:
        raise NotImplementedError("Can't measure on deprecated sensors!!!")
