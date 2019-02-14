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
