# coding=utf-8
from abc import ABC

from wetstat.hardware.sensors import counter_service
from wetstat.hardware.sensors.base_sensor import BaseSensor
from wetstat.common import logger


class CountingSensor(BaseSensor, ABC):
    @staticmethod
    def get_count(pin) -> int:
        ret = counter_service.send_command(f"get {pin}")
        logger.log.debug(f"received '{ret}' as response")
        if ret.startswith(counter_service.ERROR):
            counter_service.send_command(f"start {pin}")
            ret = 0  # it doesn't make sense to get the value right after starting the counter
        return int(ret)
