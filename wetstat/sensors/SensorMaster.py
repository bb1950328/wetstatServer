import datetime
import time

import schedule

from wetstat.sensors.TempSensor import TempSensor

SENSORS = [
    TempSensor(1),
    TempSensor(2),
]


class SensorMaster:
    def __init__(self):
        pass

    @staticmethod
    def get_sensor_for_info(name: str, value):
        for sensor in SENSORS:
            info = sensor.get_info()
            if name in info.keys():
                if info[name] == value:
                    return sensor
        return None

    @staticmethod
    def get_sensor_short_names():
        return [s.get_short_name() for s in SENSORS]

    @staticmethod
    def _measure_row(data: list, stoptime: datetime.datetime):
        data.append([s.measure() for s in SENSORS])
        if datetime.datetime.now() > stoptime:  # should stop
            return schedule.CancelJob

    @staticmethod
    def measure_now(stoptime: datetime.datetime,
                    savedate: datetime.datetime = None):
        """
        :param length: in seconds
        :param savedate: in which date the values are saved
        :return: None
        """
        heads = SensorMaster.get_sensor_short_names()

        nexttime = datetime.datetime.now() + dist

        data = []
        schedule.every(5).seconds.do(SensorMaster._measure_row,
                                     data=data,
                                     stoptime=stoptime - datetime.timedelta(seconds=5)
                                     )
