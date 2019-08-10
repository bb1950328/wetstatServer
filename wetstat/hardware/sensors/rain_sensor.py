# coding=utf-8
from wetstat.hardware.sensors import counter_service
from wetstat.hardware.sensors.base_sensor import BaseSensor, CompressionFunction

# mm per bucket calculation for rain gauges like this: https://www.aliexpress.com/item/1000001838878.html
# area of the collecting cone: 5757.5mm^2
# this is 173.686 times smaller than a square meter (10^6 / 5757.5)
# 1 Liter => 430 buckets
# 2.325ml => 1 bucket
# when it rains 1mm (= 1 Liter per m^2), the cone collects 5.7575 ml => 2.475725 buckets
# so 1 bucket must be ~0.403mm (1 / 2.475725)
#
# check:
# prism volume for 1 bucket: 2.325ml = 2325.58 mm^3
# prism footprint: 5757.5mm^2
# so prism height is 0.4039mm (2325.58 mm^3 / 5757.5mm^2)
# so the calculation is correct

MM_PER_BUCKET = (1_000_000 / 430) / 5757.5
PIN = 4  # bcm number


class RainSensor(BaseSensor):
    def get_compression_function(self) -> CompressionFunction:
        return CompressionFunction.SUM

    def get_display_color(self) -> str:
        return "#0000ff"

    def get_unit(self) -> str:
        return "mm"

    def get_long_name(self) -> str:
        return "Niederschlag"

    def get_short_name(self) -> str:
        return "Rain"

    def measure(self) -> float:
        ret = counter_service.send_command(f"get {PIN}")
        if ret.startswith(counter_service.ERROR):
            counter_service.send_command(f"start {PIN}")
            ret = 0  # it doesn't make sense to get the value right after starting the counter
        return int(ret) * MM_PER_BUCKET
