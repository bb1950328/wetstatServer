# coding=utf-8
from abc import ABC

from wetstat.hardware.sensors import counter_service
from wetstat.hardware.sensors.base_sensor import BaseSensor


class CountingSensor(BaseSensor, ABC):
    @staticmethod
    def get_count(pin) -> int:
        ret = counter_service.send_command(f"get {pin}")
        if ret.startswith(counter_service.ERROR):
            counter_service.send_command(f"start {pin}")
            ret = 0  # it doesn't make sense to get the value right after starting the counter
        return int(ret)
