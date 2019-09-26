# coding=utf-8

from wetstat.hardware.sensors.abstract.bme280_base import BME280Base


class HumiditySensor(BME280Base):

    def get_long_name(self) -> str:
        return "rel. Luftfeuchte"

    def get_short_name(self) -> str:
        return "Humidity"

    def get_display_color(self) -> str:
        return "#0effe2"

    def get_unit(self) -> str:
        return "%"

    def measure(self) -> float:
        return self.get_sample().humidity
