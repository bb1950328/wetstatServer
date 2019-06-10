# coding=utf-8
from datetime import datetime, timedelta
from typing import Optional, List

from django.http import QueryDict

from wetstat.hardware.sensors.SensorMaster import SensorMaster
from wetstat.model.custom_plot.custom_plot import CustomPlot
from wetstat.model.custom_plot.sensor_options import CustomPlotSensorOptions
from wetstat.view import views


class CustomPlotRequest:

    def __init__(self, get: QueryDict):
        self.get: QueryDict = get
        self.custom_plot: Optional[CustomPlot] = None

    def parse_start_end(self):
        start: str = self.get.get("start")
        end: str = self.get.get("end")
        if start is not None and end is not None:
            if not len(start) or not len(end):
                raise ValueError("Start and/or end empty!")
        else:
            raise ValueError("Start and/or end not specified!")
        try:
            if start.startswith("now-"):
                def make_absolute(inp: str):
                    return views.get_date() - \
                           timedelta(seconds=int(
                               inp.split("-")[1]  # remove "now-"
                           ))

                start_dt = make_absolute(start)
                end_dt = make_absolute(end)
            else:
                try:
                    start_dt = datetime.fromtimestamp(int(start) / 1000)
                    end_dt = datetime.fromtimestamp(int(end) / 1000)
                except ValueError:
                    start_dt = datetime.fromisoformat(start)
                    end_dt = datetime.fromisoformat(end)
        except ValueError or OSError as e:
            raise ValueError("Start and/or end has wrong format!") from e
        return start_dt, end_dt

    def parse(self):
        self.custom_plot = CustomPlot()
        start_dt, end_dt = self.parse_start_end()
        self.custom_plot.set_start(start_dt)
        self.custom_plot.set_end(end_dt)

        for key in self.get.keys():
            if key == "start" or key == "end":
                continue  # already processed
            value: List[str] = self.get.getlist(key)
            if isinstance(value, str):
                value = [value]
            if key == "line":
                # value = "short_name,axis,minmaxavg_interval,linecolor
                #         |     0    |  1 |       2          |    3    |
                for line_value in value:
                    args: List[Optional[str]] = line_value.split(sep=",")
                    if len(args) < 4:
                        raise ValueError("too less arguments in line \"{}\"".format(line_value))
                    try:
                        sensor = SensorMaster.get_sensor_for_info("short_name", args[0])
                        so = CustomPlotSensorOptions(sensor)
                        if args[1] != "auto":
                            so.set_axis(args[1])
                        if args[2] == "none":
                            args[2] = None
                        so.set_minmaxavg_interval(args[2])
                        if args[3] != "auto":
                            args[3] = args[3].replace("_35", "#")
                            so.set_line_color(args[3])
                        self.custom_plot.add_sensoroption(so)
                    except ValueError as e:
                        raise ValueError("Error parsing line \"{}\" ({})".format(line_value, str(e))) from e
            elif key == "legend_mode":
                try:
                    mode = int(value[0])
                    self.custom_plot.set_legend_mode(mode)
                except ValueError as e:
                    raise ValueError("Invalid legend_mode ({})".format(value[0])) from e
            elif key == "title":
                self.custom_plot.set_title(value[0])
            elif key == "aspect_ratio":
                try:
                    x, y = value[0].split(":")
                    x = int(x)
                    y = int(y)
                    self.custom_plot.figsize = (x, y)
                except ValueError or IndexError as e:
                    raise ValueError("invalid aspect_ratio! (should be something like \"16:9\")") from e
