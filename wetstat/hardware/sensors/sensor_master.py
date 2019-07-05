# coding=utf-8
import datetime
import os
import threading
import time
from typing import Optional, List

import numpy as np
import schedule

from wetstat.common import logger, config
from wetstat.hardware.sensors.base_sensor import BaseSensor
from wetstat.hardware.sensors.fake_sensor import FakeSensor
from wetstat.hardware.sensors.old_light_sensor import OldLightSensor
from wetstat.hardware.sensors.old_temp_sensor import OldTempSensor
from wetstat.hardware.sensors.temp_sensor import TempSensor
from wetstat.model import csvtools, util

# Old Sensors
ALL_SENSORS: List[BaseSensor] = [
    OldTempSensor(2),
    OldLightSensor(),
]
if not config.on_pi():
    ALL_SENSORS.extend([
        TempSensor(1),
        TempSensor(2),
    ])

USED_SENSORS: List[BaseSensor] = [
    # Used sensors on Pi
    TempSensor(1),
    TempSensor(2),
] if config.on_pi() else [
    # Used sensors on other PCs
    FakeSensor(1),
    FakeSensor(2),
]

ALL_SENSORS.extend(USED_SENSORS)

schedule.logger.setLevel(schedule.logging.ERROR)

measuring_allowed = True
measuring_allowed_lock = threading.Lock()


def stop_measuring() -> None:
    with measuring_allowed_lock:
        global measuring_allowed
        measuring_allowed = False


class SensorMaster:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_sensor_for_info(name: str, value) -> Optional[BaseSensor]:
        for sensor in ALL_SENSORS:
            info = sensor.get_info()
            if name in info.keys() and info[name] == value:
                return sensor
        return None

    @staticmethod
    def get_sensor_short_names() -> List[str]:
        return [s.get_short_name() for s in USED_SENSORS]

    @staticmethod
    def _measure_row(data: list, stoptime: datetime.datetime):
        data.append([s.measure() for s in USED_SENSORS])
        if datetime.datetime.now() > stoptime:  # should stop
            return schedule.CancelJob

    @staticmethod
    def measure_now(stoptime: datetime.datetime,
                    savedate: datetime.datetime = None):
        """
        :param stoptime: timestamp on which the measurement should be finished
        :param savedate: under which date the values are saved
        :return: None
        """
        heads = SensorMaster.get_sensor_short_names()

        data = []
        schedule.every(5).seconds.do(SensorMaster._measure_row,
                                     data=data,
                                     stoptime=stoptime - datetime.timedelta(seconds=10)
                                     )
        while len(schedule.jobs):
            schedule.run_pending()
            with measuring_allowed_lock:
                if not measuring_allowed:
                    return
            time.sleep(1)
        means = list(np.mean(data, axis=0))
        means = [round(n, 3) for n in means]
        logger.log.debug(f"measured values {str(means)}")
        path = csvtools.save_values(config.get_datafolder(), heads, means, savedate)
        logger.log.debug(f"saved values in {os.path.basename(path)}")

    @staticmethod
    def measure(freq: int = 600):
        """
        measures values forever
        :param freq: measuring frequency in seconds
        :return: None
        """

        next_stop = util.round_time(round_to=120, mode=1)  # next even minute
        while True:
            # noinspection PyBroadException
            try:
                SensorMaster.measure_now(next_stop, next_stop)
                logger.log.info("Measured and saved under label '" + next_stop.isoformat() + "'")
                with measuring_allowed_lock:
                    if not measuring_allowed:
                        logger.log.info("Measuring stopped.")
                        return
                next_stop += datetime.timedelta(seconds=freq)
                now = datetime.datetime.now()
                if next_stop < now:
                    logger.log.warning(f"Time jump from {next_stop.isoformat()} to {now.isoformat()}")
                    next_stop = util.round_time(round_to=120, mode=1)

            except Exception:
                logger.log.exception("Exception occurred in SensorMaster.measure")
