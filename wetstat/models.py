# coding=utf-8
import os
import os.path
from datetime import datetime, timedelta
from time import perf_counter_ns
from typing import Callable, List, Tuple, Dict, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from django.http import QueryDict
from matplotlib.image import imread, imsave
from numpy import ndarray

from wetstat import csvtools, config, logger, views
from wetstat.csvtools import DataContainer
from wetstat.sensors.BaseSensor import BaseSensor
from wetstat.sensors.SensorMaster import SensorMaster


class WetstatModel:
    def __init__(self):
        pass


"""class DayData:
    date: datetime.date
    array: np.array
    fields: list

    def __init__(self, date: datetime.date, array: np.array, fields: list):
        self.date = date
        self.array = array
        self.fields = fields
"""


def generate_plot(container: csvtools.DataContainer,
                  num_xticks,
                  useaxis=None,  # 0: do not plot, 1: first axis, 2: second axis
                  linecolors=None,
                  yaxis1label="Temperature",
                  yaxis2label="Light Intensity",
                  dateformat="%d.%m.%y %H:%M",
                  rotation=90,
                  title=None,
                  make_minmaxavg=None,  # list of bool
                  linewidth=0.75,
                  figsize=(16, 9),
                  dpi=100,
                  make_tooltips=True,
                  filename=None):
    if make_minmaxavg is None:
        make_minmaxavg = []
    if title is None:
        title = "Weather from "
        title += container.data[0].date.strftime("%d.%m.%y")
        title += " to "
        title += container.data[-1].date.strftime("%d.%m.%y")
    if linecolors is None:
        linecolors = ["red", "green", "blue", "orange"]
    if useaxis is None:
        useaxis = [1, 0, 2]
    d = container.data[0].array
    days = len(container.data)
    for i in range(1, days):
        d = np.concatenate((d, container.data[i].array))
    datalength = len(d)
    print(datalength, "values to plot (", days, "days)")
    xtick_pos = np.linspace(0, datalength, num=num_xticks)
    xtick_str = []
    for p in xtick_pos:
        idx = int(p)
        if idx >= datalength:
            idx -= 1
        xtick_str.append(d[idx][0].strftime(dateformat))
    fig, ax1 = plt.subplots(figsize=figsize, dpi=dpi)
    plt.sca(ax1)
    plt.xticks(xtick_pos, xtick_str, rotation=rotation)
    ax1.xaxis.grid(True, linestyle="-")
    ax1.yaxis.grid(True, linestyle="-")
    ax1.set_ylabel(yaxis1label)
    ax2 = ax1.twinx()
    ax2.set_ylabel(yaxis2label)
    plt.title(title, pad=30)
    plt.xlim([0, datalength])
    for i in range(len(useaxis)):
        yes = False
        if i < len(make_minmaxavg):
            yes = make_minmaxavg[i]
        if yes and useaxis[i]:
            max_arr = []
            min_arr = []
            avg_arr = []
            for day in container.data:
                min_arr.append(np.amin(day.array[:, i + 1]))
                max_arr.append(np.amax(day.array[:, i + 1]))
                avg_arr.append(np.mean(day.array[:, i + 1]))
            max_arr = np.array(max_arr)
            min_arr = np.array(min_arr)
            avg_arr = np.array(avg_arr)
            axis = ax1
            if useaxis[i] == 2:
                axis = ax2
            name = container.data[0].fields[i + 1]
            x = np.linspace(0, datalength, num=days)
            axis.plot(x, max_arr, color=linecolors[i], linewidth=linewidth * 0.7)
            axis.plot(x, min_arr, color=linecolors[i], linewidth=linewidth * 0.7)
            axis.plot(x, avg_arr, color=linecolors[i], linewidth=linewidth * 1.2, label=name + " Day AVG")
            axis.fill_between(x, max_arr, min_arr, color=linecolors[i], alpha=0.2)
            useaxis[i] = 0  # avoid plotting that data twice
            if i == 0 and make_tooltips:
                pass
                # TODO
                # labels = ['point {0}'.format(i + 1) for i in range(datalength)]
                # tooltip = mpld3.plugins.PointLabelTooltip(avg_arr, labels)
                # mpld3.plugins.connect(fig, tooltip)

    # experimental
    # ax2.set_yscale('log')
    for i, name in enumerate(container.data[0].fields):
        if i == 0:
            continue  # skip time column
        if useaxis[i - 1]:
            axis = ax1
            if useaxis[i - 1] == 2:
                axis = ax2
            axis.plot(range(datalength), d[:, i], label=name, color=linecolors[i - 1], linewidth=linewidth)
    fig.tight_layout()
    fig.legend(loc="upper center", ncol=20, fancybox=True, shadow=True, bbox_to_anchor=(0.5, 0.945))
    if filename is not None:
        plt.savefig(filename)
    fig.show()


def get_nearest_record(dt: datetime) -> dict:  # (field: value)
    try:
        day = csvtools.load_csv_to_daydata(os.path.join(config.get_datafolder(),
                                                        csvtools.get_filename_for_date(dt)))
        i = 0
        while (len(day.array) > i) and (day.array[i][0] < dt):
            i += 1
        arr = day.array[i]
        ret = {}
        for i, name in enumerate(day.fields):
            ret[name] = arr[i]
        return ret
    except FileNotFoundError as e:
        raise ValueError("No data available for date " + dt.isoformat()) from e


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


class CustomPlot:
    # Type hints:
    message_container: Optional[views.MessageContainer]
    plot_id: Optional[str]
    legend_mode: int
    legends: Optional[Dict[str, str]]
    xtick_str: Optional[Union[List[str], ndarray]]
    xtick_pos: Optional[Union[List[Union[datetime, float]], ndarray]]
    lines_of_axes: Optional[List[List[List[str]]]]
    vectorized_from_ts: Callable
    datalines: Optional[Dict[str, Tuple]]
    title: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]
    sensoroptions: Dict[str, CustomPlotSensorOptions]
    axislabels: Optional[dict]
    data: Optional[DataContainer]
    dpi: int
    figsize: Tuple[int, int]
    linewidth: float
    axes: List[Optional[list]]
    filename: Optional[str]

    def __init__(self):
        self.filename = None
        self.legends = None
        self.linewidth = 0.75
        self.dateformat = "%d.%m.%y %H:%M"
        self.xtick_str = None
        self.xtick_pos = None
        self.figsize = (16, 9)
        self.dpi = 120
        self.axes = []  # axes[0] is ["label left", "label right"]
        self.data = None
        self.datalines = None  # dict, key: shortname of sensor, value: (x: np.array, y: np.array)
        self.sensoroptions = {}  # dict, key=shortname, value=CustomPlotSensorOptions
        self.start = None
        self.end = None
        self.title = None
        self.axislabels = None  # dict, key: for example "1b", value: label
        self.lines_of_axes = None  # list [[["Temp3", "Light2"], ["...", "..."]], [["...", "..."], ["...", "..."]]]
        self.max_xticks = 24
        self.vectorized_from_ts = np.vectorize(datetime.fromtimestamp)
        self.legend_mode = 0  # 0=inside plot, 1=save in separate file, 2=no legend
        self.plot_id = None
        self.message_container = None

    def set_legend_mode(self, legend_mode: int):
        if 0 <= legend_mode <= 2:
            self.legend_mode = legend_mode
        else:
            raise ValueError("legend_mode not in range!!, see comment in __init__()")

    def add_sensoroption(self, option: CustomPlotSensorOptions):
        for op in self.sensoroptions.values():
            if hash(op) == option:
                return  # already in list
        hrh = option.hr_hash()
        self.sensoroptions[hrh] = option

    def get_sensoroptions(self) -> dict:
        return self.sensoroptions

    def set_start(self, start: datetime):
        now = datetime.now()
        if start > now:
            raise ValueError("Start must be before now!")
        if self.end is not None and self.end < start:
            raise ValueError("Start must be before end!")
        self.start = start

    def get_start(self):
        return self.start

    def set_end(self, end: datetime):
        now = datetime.now()
        if end > now:
            raise ValueError("End must be before now!")
        if self.start is not None and self.start > end:
            raise ValueError("End must be after start!")
        self.end = end

    def get_end(self):
        return self.end

    def check_data_exists(self):
        """
        :return: filename of the first missing file, None if everything is ok
        """
        if self.start is None or self.end is None:
            raise ValueError("Start and end have to be set when calling this method!")
        oneday = timedelta(days=1)
        i = self.start
        files = []
        while i < self.end:
            files.append(csvtools.get_filename_for_date(i))
            i = i + oneday
        datafolder = csvtools.get_data_folder()
        for file in files:
            path = os.path.join(datafolder, file)
            if not os.path.isfile(path):
                return file
        return None

    def load_data(self, ignore_missing=True):
        missing = ((not ignore_missing) and self.check_data_exists())
        if missing:
            raise FileNotFoundError("Data does not exist! (at least " + missing + ") missing")
        if self.data is not None:
            # data already here
            return
        self.data = csvtools.load_csv_for_range(csvtools.get_data_folder(),
                                                self.start, self.end,
                                                ignore_missing=ignore_missing)

    def add_message(self, message: str):
        timestamp = (perf_counter_ns() - self.start_ts) / 10 ** 9
        if self.plot_id is not None and self.message_container is not None:
            self.message_container.add_message(self.plot_id, str(round(timestamp, 3)).ljust(6) + ": " + message)

    def set_title(self, title: str):
        self.title = title

    def get_title(self):
        if self.title is not None:
            return self.title
        elif self.start is not None and self.end is not None:
            self.title = "Weather from "
            self.title += self.start.strftime("%d.%m.%y")
            self.title += " to "
            self.title += self.end.strftime("%d.%m.%y")
        return self.title

    def set_all_linecolors(self):
        standards = ["red", "green", "blue", "orange", "black", "yellow", "black"]
        for key, sensor in self.sensoroptions.items():
            color = sensor.get_line_color()
            if not color:
                sensor.set_line_color(standards.pop(0))  # remove first
            elif color in standards:
                standards.remove(color)

    def split_data_to_lines(self):
        if self.datalines is not None:
            return  # Already splitted
        else:
            self.datalines = {}
        for hr_hash in self.sensoroptions:
            short_name = self.sensoroptions[hr_hash].get_sensor().get_short_name()
            x = np.array([])
            y = np.array([])
            for day in self.data.data:
                if short_name in day.fields:
                    x = np.append(x, day.array[:, 0])
                    # debug:
                    y = np.append(y, day.array[:, day.fields.index(short_name)])
            x = [d.timestamp() for d in x]
            self.datalines[hr_hash] = (x, y)

    def make_all_lines_minmaxavg(self):
        for hr_hash in self.sensoroptions:
            if self.sensoroptions[hr_hash].get_minmaxavg_interval() is not None:
                self.make_line_minmaxavg(hr_hash)

    def make_line_minmaxavg(self, hr_hash):
        """
        :param hr_hash: key of self.sensoroptions
        :return: True when something changed, otherwise False
        """
        options = self.sensoroptions[hr_hash]
        interval = options.get_minmaxavg_interval()
        x, y = self.datalines[hr_hash]
        x_dt = self.vectorized_from_ts(x)
        x_new = []
        miny = np.array([])
        maxy = np.array([])
        avgy = np.array([])
        if interval == "day":
            relevant: Callable[[datetime], datetime.date] = lambda dt: dt.date()
        elif interval == "hour":
            relevant: Callable[[datetime], int] = lambda dt: dt.hour
        elif interval == "week":
            relevant: Callable[[datetime], int] = lambda dt: int(dt.strftime("%W"))  # week of year
        elif interval == "month":
            relevant: Callable[[datetime], int] = lambda dt: dt.month
        elif interval == "year":
            relevant: Callable[[datetime], int] = lambda dt: dt.year
        else:
            raise ValueError("interval of {} is None or unknown!".format(hr_hash))

        istart = 0
        iend = 1
        while iend < len(x):
            while iend < len(x) and (relevant(x_dt[istart]) == relevant(x_dt[iend])):
                iend += 1
            miny = np.append(miny, np.amin(y[istart:iend]))
            maxy = np.append(maxy, np.amax(y[istart:iend]))
            avgy = np.append(avgy, np.mean(y[istart:iend]))
            idx = int((istart + iend) // 2)  # median
            x_new.append(x_dt[idx].timestamp())
            istart = iend
            iend = istart + 1

        self.datalines[hr_hash] = (x_new, (miny, maxy, avgy))
        return True

    def prepare_axis_labels(self):
        if self.axislabels is not None:
            return
        self.axislabels = {}
        for hr_hash, option in self.sensoroptions.items():
            label = option.get_sensor().get_long_name() + \
                    " [" + option.get_sensor().get_unit() + "]"
            axis = option.get_axis()
            if axis in self.axislabels.keys():
                if self.axislabels[axis] != label:
                    self.axislabels[axis] += (", " + label)
            else:
                self.axislabels[axis] = label
        for axCode in self.axislabels:
            label = self.axislabels[axCode]
            i = int(axCode[0])
            a_or_b = axCode[1]

            while len(self.axes) <= i:
                self.axes.append(None)

            if self.axes[i] is not None:
                sa, sb = self.axes[i]
            else:
                sa, sb = None, None

            if a_or_b == "a":
                sa = label
            else:
                sb = label
            self.axes[i] = [sa, sb]
        self.axes = list(filter(lambda x: x is not None, self.axes))

    def distribute_lines_to_axes(self):
        self.lines_of_axes = []
        numbers = [(0 if so.get_axis() is None else int(so.get_axis()[0])) for so in self.sensoroptions.values()]
        ma = max(set(numbers))  # set(...) to remove duplicates
        for i in range(ma + 1):
            self.lines_of_axes.append([[], []])
        format_axis: Callable[[int, int], str] = lambda ii, nn: str(ii) + ("a" if nn == 0 else "b")
        for hr_hash, option in self.sensoroptions.items():
            if option.get_axis() is None:
                not_found = True
                for i in range(len(self.lines_of_axes)):
                    for n in range(2):
                        short_names = self.lines_of_axes[i][n]
                        if short_names:
                            sensor = self.sensoroptions[hr_hash].get_sensor()
                            if sensor.get_unit() == option.get_sensor().get_unit():
                                print(f"Distributed SO {hr_hash} to ax {i}, {n} with same unit")
                                self.lines_of_axes[i][n].append(hr_hash)
                                option.set_axis(format_axis(i, n))
                                not_found = False
                if not_found:
                    for i in range(len(self.lines_of_axes)):
                        for n in range(2):
                            if not self.lines_of_axes[i][n] and not_found:
                                self.lines_of_axes[i][n].append(hr_hash)
                                option.set_axis(format_axis(i, n))
                                print(f"Distributed SO {hr_hash} to empty ax {i}, {n}")
                                not_found = False
                if not_found:
                    self.lines_of_axes.append([[hr_hash], []])
                    option.set_axis(format_axis(len(self.lines_of_axes), 0))
                    print(f"Distributed SO {hr_hash} to new ax")
                    continue
            else:
                ax = int(option.get_axis()[0])
                ab = option.get_axis()[1].lower()
                n = (0 if ab == "a" else 1)
                self.lines_of_axes[ax][n].append(hr_hash)

        self.lines_of_axes = list(filter(lambda x: not (len(x[0]) == 0 and len(x[1]) == 0),
                                         self.lines_of_axes))  # remove empty subplots

    def generate_xticks(self):
        if self.data is None:
            raise ValueError("Load data first!!")
        self.xtick_pos = []
        self.xtick_str = []
        start = self.data.data[0].array[0, 0].timestamp()
        end = self.data.data[-1].array[-1, 0].timestamp()

        self.xtick_pos = np.linspace(start, end, self.max_xticks)
        self.xtick_pos = self.vectorized_from_ts(self.xtick_pos)
        self.xtick_str = np.array([pos.strftime(self.dateformat) for pos in self.xtick_pos])
        self.xtick_pos = [d.timestamp() for d in self.xtick_pos]

    def generate_legends(self):
        self.legends = {hr_hash: op.get_sensor().get_long_name() + op.get_minmaxavg_interval_for_legend()
                        for hr_hash, op in self.sensoroptions.items()}

    @staticmethod
    def save_legend(legend, filename="legend.png", expand=None, crop=4):
        if expand is None:
            expand = [-5, -5, 5, 5]
        fig = legend.figure
        fig.canvas.draw()
        bbox = legend.get_window_extent()
        bbox = bbox.from_extents(*(bbox.extents + np.array(expand)))
        bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(filename, dpi="figure", bbox_inches=bbox)
        if crop > 0:
            img = imread(filename)
            w, h, d = img.shape
            img = img[crop:w - crop, crop:h - crop]
            imsave(filename, img)

    def create_plots(self):
        self.start_ts = perf_counter_ns()  # self only for debug
        self.add_message("Lade Daten")
        self.load_data()
        self.add_message("Setze Farben")
        self.set_all_linecolors()
        self.add_message("Verteile Datenreihen")
        self.distribute_lines_to_axes()
        self.add_message("Bereite Beschriftungen vor")
        self.prepare_axis_labels()
        self.add_message("Generiere X-Beschriftungen")
        self.generate_xticks()
        self.add_message("Teile Daten auf")
        self.split_data_to_lines()
        self.add_message("Verkleinere Daten")
        self.make_all_lines_minmaxavg()
        self.add_message("Generiere Legenden")
        self.generate_legends()
        self.add_message("Erzeuge Zeichenbereich")
        fig, subs = plt.subplots(nrows=len(self.axes), sharex="all", figsize=self.figsize, dpi=self.dpi)
        if len(self.axes) < 2:
            subs = [subs]
        self.add_message("Setze X-Beschriftungen")
        plt.xticks(self.xtick_pos, self.xtick_str, rotation=90)
        plt.xlim(self.xtick_pos[0], self.xtick_pos[-1])
        num_lines = len(self.sensoroptions.keys())
        num_actual_line = 0
        for i_subplt, subplt in enumerate(subs):
            subplt.xaxis.grid(True, linestyle="-")
            labels = self.axes[i_subplt]
            left_axis = subplt
            right_axis = subplt.twinx()
            left_axis.set_ylabel(labels[0])
            right_axis.set_ylabel(labels[1])
            lines = self.lines_of_axes[i_subplt]
            all_lines = lines[0] + lines[1]
            for hr_hash in all_lines:
                num_actual_line += 1
                self.add_message(f"Zeichne Linie {num_actual_line} von {num_lines}")
                axis = (left_axis if hr_hash in lines[0] else right_axis)
                option = self.sensoroptions[hr_hash]
                x, y = self.datalines[hr_hash]
                color = option.get_line_color()
                label = self.legends[hr_hash]
                if option.get_minmaxavg_interval() is not None:
                    miny, maxy, avgy = y
                    axis.plot(x, maxy, color=color, linewidth=self.linewidth * 0.7)
                    axis.plot(x, miny, color=color, linewidth=self.linewidth * 0.7)
                    axis.plot(x, avgy, color=color, linewidth=self.linewidth * 1.2,
                              label=label)
                    axis.fill_between(x, maxy, miny, color=color, alpha=0.2)
                else:
                    axis.plot(x, y, label=label, color=color, linewidth=self.linewidth)
        title = plt.suptitle(self.get_title(), y=1.0, size=32)

        """bbox_extra_artists = (title,)
        if self.filename is not None:
            filename_ext = os.path.splitext(self.filename)[1]
            if len(filename_ext) == 0:
                filename_ext = ".svg"
                self.filename += filename_ext
        if self.legend_mode == 0:  # inside
            lgd = fig.legend(loc="upper center", ncol=20, fancybox=True, shadow=True, bbox_to_anchor=(0.5, 0.97))
            bbox_extra_artists = (lgd, title)
        elif self.legend_mode == 1:  # separate file
            lgd = fig.legend(ncol=1, loc=5, framealpha=1, frameon=True)
            if self.filename is not None:
                self.save_legend(lgd, filename=self.filename + "_legend" + filename_ext)
            lgd.remove()
        if self.filename is not None:
            plt.savefig(self.filename, bbox_extra_artists=bbox_extra_artists, bbox_inches='tight')
            
        ###################################################################################################"""
        self.add_message("Speichere Graph")
        bbox_extra_artists = (title,)
        if self.legend_mode == 0:  # legend inside
            lgd = fig.legend(loc="upper center", ncol=20, fancybox=True, shadow=True, bbox_to_anchor=(0.5, 0.97))
            bbox_extra_artists = (lgd, title)
        if self.filename is not None:  # we have to export the plot to file
            filename_ext = os.path.splitext(self.filename)[1]
            if len(filename_ext) == 0:
                filename_ext = ".svg"
                self.filename += filename_ext
            if self.legend_mode == 1:  # legend in separate file
                lgd = fig.legend(ncol=1, loc=5, framealpha=1, frameon=True)
                if self.filename is not None:
                    self.save_legend(lgd, filename=self.filename + "_legend.png")
                lgd.remove()
            plt.savefig(self.filename, bbox_extra_artists=bbox_extra_artists, bbox_inches='tight')

        end_ts = perf_counter_ns()
        time_used = (end_ts - self.start_ts) / 10 ** 9
        logger.log.info("custom plot creation finished in {} sec.".format(time_used))
        # fig.show()
        self.add_message("Fertig")
        self.add_message("%%finished%%")
        return time_used


class CustomPlotRequest:
    custom_plot: Optional[CustomPlot]
    get: QueryDict
    DATEFORMAT = ""

    def __init__(self, get: QueryDict):
        self.get = get
        self.custom_plot = None

    def parse(self):
        self.custom_plot = CustomPlot()
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
            self.custom_plot.set_start(start_dt)
            self.custom_plot.set_end(end_dt)
        except ValueError or OSError as e:
            raise ValueError("Start and/or end has wrong format!") from e
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
                    args = line_value.split(sep=",")
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


def cleanup_plots(max_age=timedelta(days=2)):
    plotfolder = os.path.join(config.get_staticfolder(), "plot")
    files = list(filter(os.path.isfile,
                        os.listdir(plotfolder)))
    split_dt = datetime.now() - max_age
    to_delete = []
    for f in files:
        fullpath = os.path.join(plotfolder, f)
        lastaccess = datetime.fromtimestamp(os.path.getatime(fullpath))
        if lastaccess < split_dt:
            to_delete.append(fullpath)
    if len(to_delete) > 0:
        logger.log.info(f"Deleting {len(to_delete)} plots because they are older than {str(max_age)}")
        for f in to_delete:
            os.remove(f)
