# coding=utf-8
import os
import random
from datetime import datetime, timedelta
from time import perf_counter_ns
from typing import Optional, Dict, Union, List, Callable, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.image import imread, imsave
from numpy.core.multiarray import ndarray

from wetstat.common import logger, config
from wetstat.model import csvtools
from wetstat.model.csvtools import DataContainer
from wetstat.model.custom_plot.sensor_options import CustomPlotSensorOptions
from wetstat.view.message_container import MessageContainer


class CustomPlot:
    # Type hints:
    message_container: Optional[MessageContainer]
    plot_id: str
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

    def __init__(self) -> None:
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
        self.plot_id = hex(random.randint(0x1000000000000, 0xfffffffffffff))[2:]
        self.message_container = None
        self.PERCENTS = [0, 5.64786686, 5.650508519, 5.692775063, 5.695416722, 5.748249901, 6.020340774, 8.017434949,
                         8.020076608, 23.36547352, 29.54695549, 30.09906221, 100, 100]

    def get_plot_id(self) -> str:
        return self.plot_id

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

    def get_start(self) -> datetime:
        return self.start

    def set_end(self, end: datetime):
        now = datetime.now()
        if end > now:
            raise ValueError("End must be before now!")
        if self.start is not None and self.start > end:
            raise ValueError("End must be after start!")
        self.end = end

    def get_end(self) -> datetime:
        return self.end

    def check_data_exists(self) -> Optional[str]:
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
        datafolder = config.get_datafolder()
        for file in files:
            path = os.path.join(datafolder, file)
            if not os.path.isfile(path):
                return file
        return None

    def load_data(self, ignore_missing: bool = True) -> Optional[DataContainer]:
        missing = ((not ignore_missing) and self.check_data_exists())
        if missing:
            raise FileNotFoundError("Data does not exist! (at least " + missing + ") missing")
        if self.data is not None:
            # data already here
            return
        self.data = csvtools.load_csv_for_range(config.get_datafolder(),
                                                self.start, self.end,
                                                ignore_missing=ignore_missing)

    def add_message(self, message: str, percent=None):
        timestamp = (perf_counter_ns() - self.start_ts) / 10 ** 9
        if self.plot_id is not None and self.message_container is not None:
            pstr = ""
            self.message_container.add_message(self.plot_id, pstr + str(round(timestamp, 3)) + ": " + message)
            if percent is not None:
                self.message_container.set_percent(self.plot_id, percent)
                self.message_container.set_percent_per_second(self.plot_id, percent / timestamp)

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
        for ax_code in self.axislabels:
            label = self.axislabels[ax_code]
            i = int(ax_code[0])
            a_or_b = ax_code[1]

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
                                # print(f"Distributed SO {hr_hash} to ax {i}, {n} with same unit")
                                self.lines_of_axes[i][n].append(hr_hash)
                                option.set_axis(format_axis(i, n))
                                not_found = False
                if not_found:
                    for i in range(len(self.lines_of_axes)):
                        for n in range(2):
                            if not self.lines_of_axes[i][n] and not_found:
                                self.lines_of_axes[i][n].append(hr_hash)
                                option.set_axis(format_axis(i, n))
                                # print(f"Distributed SO {hr_hash} to empty ax {i}, {n}")
                                not_found = False
                if not_found:
                    self.lines_of_axes.append([[hr_hash], []])
                    option.set_axis(format_axis(len(self.lines_of_axes), 0))
                    # print(f"Distributed SO {hr_hash} to new ax")
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
        # percents = [0.00, 47.07, 47.07, 47.07, 47.07, 47.09, 65.86, 86.72, 86.72, 87.34, 88.38, 88.82, 95.87, 100.00]
        ##debug:
        try:
            self.start_ts = perf_counter_ns()  # self only for debug
            self.add_message("Lade Daten", self.PERCENTS[0])
            self.load_data()
            after_load_ts = perf_counter_ns()
            pps = self.PERCENTS[1] / ((after_load_ts - self.start_ts) / (10 ** 9))
            self.message_container.set_percent_per_second(self.plot_id, pps)
            self.add_message("Setze Farben", self.PERCENTS[1])
            self.set_all_linecolors()
            self.add_message("Verteile Datenreihen", self.PERCENTS[2])
            self.distribute_lines_to_axes()
            self.add_message("Bereite Beschriftungen vor", self.PERCENTS[3])
            self.prepare_axis_labels()
            self.add_message("Generiere X-Beschriftungen", self.PERCENTS[4])
            self.generate_xticks()
            self.add_message("Teile Daten auf", self.PERCENTS[5])
            self.split_data_to_lines()
            self.add_message("Verkleinere Daten", self.PERCENTS[6])
            self.make_all_lines_minmaxavg()
            self.add_message("Generiere Legenden", self.PERCENTS[7])
            self.generate_legends()
            self.add_message("Erzeuge Zeichenbereich", self.PERCENTS[8])
            fig, subs = plt.subplots(nrows=len(self.axes), sharex="all", figsize=self.figsize, dpi=self.dpi)
            if len(self.axes) < 2:
                subs = [subs]
            self.add_message("Setze X-Beschriftungen", self.PERCENTS[9])
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

            self.add_message("Speichere Graph", self.PERCENTS[-3])
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
            self.add_message("Fertig", 100)
            self.add_message("%%finished%%", 100)
            return time_used
        except Exception:
            logger.log.exception("Exception raised while generating CustomPlot!")
            return -1
