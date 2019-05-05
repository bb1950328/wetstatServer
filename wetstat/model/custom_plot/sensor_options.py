# coding=utf-8
from typing import Optional

from wetstat.sensors.BaseSensor import BaseSensor


class CustomPlotSensorOptions:
    axis: Optional[str]
    line_color: Optional[str]
    minmaxavg_interval: Optional[str]
    sensor: Optional[BaseSensor]

    def __init__(self, sensor: BaseSensor):
        self.sensor = None
        self.set_sensor(sensor)
        self.minmaxavg_interval = None
        self.line_color = None
        self.axis = None

    def set_minmaxavg_interval(self, interval: str):
        """
        Sets the interval for MinMaxAvg
        :param interval: None=disable, "day"=day, "hour"=hour
        :return: None
        """
        allowed = [None, "day", "hour", "month", "year", "week"]
        if interval in allowed:
            self.minmaxavg_interval = interval
        else:
            raise ValueError("Wrong parameter, has to be " + "or".join(allowed))

    def get_minmaxavg_interval(self) -> str:
        return self.minmaxavg_interval

    def get_minmaxavg_interval_for_legend(self) -> str:
        if self.minmaxavg_interval is None:
            return ""
        elif self.minmaxavg_interval == "hour":
            return " (Stunde)"
        elif self.minmaxavg_interval == "day":
            return " (Tag)"
        elif self.minmaxavg_interval == "week":
            return " (Woche)"
        elif self.minmaxavg_interval == "month":
            return " (Monat)"
        elif self.minmaxavg_interval == "year":
            return " (Jahr)"
        else:
            return ""

    def set_line_color(self, color: str):
        self.line_color = color

    def get_line_color(self) -> str:
        return self.line_color

    def set_sensor(self, sensor: BaseSensor):
        if not issubclass(type(sensor), BaseSensor):
            raise ValueError("sensor has to be a subclass of BaseSensor!")
        self.sensor = sensor

    def get_sensor(self) -> BaseSensor:
        return self.sensor

    def get_axis(self) -> str:
        return self.axis

    def set_axis(self, axis: str):
        """
        :param axis: 1a=1st plot, left y axis
                     3b=3rd plot, right y axis
        :return: None
        """
        axis = axis.lower()
        if len(axis) != 2:
            raise ValueError("len(axis) should be 2!")
        if not axis[0].isdigit():
            raise ValueError("axis[0] should be digit!")
        if axis[1] != "a" and axis[1] != "b":
            raise ValueError("axis[1] should be 'a' or 'b'!")
        self.axis = axis

    def __hash__(self):
        return hash(self.hr_hash())

    def hr_hash(self) -> str:
        """
        :return: human readable hash, str
        """
        return (str(self.sensor.get_short_name()) +
                str(self.line_color) +
                str(self.minmaxavg_interval) +
                str(self.axis))
