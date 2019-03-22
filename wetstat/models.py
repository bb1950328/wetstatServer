import datetime
import os

import matplotlib.pyplot as plt
import mpld3
import numpy as np

from wetstat import csvtools, config
from wetstat.sensors.BaseSensor import BaseSensor


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
                  makeTooltips=True,
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
            if i == 0 and makeTooltips:
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


def get_nearest_record(dt: datetime.datetime) -> dict:  # (field: value)
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
        raise ValueError("No data available for date " + dt.isoformat())


class CustomPlot:
    class CustomPlotSensorOptions:
        def __init__(self, sensor: BaseSensor):
            self.sensor = None
            self.set_sensor(sensor)
            self.minmaxavg_interval = None
            self.line_color = None
            self.axis = None

        def set_minmaxavg_interval(self, interval):
            """
            Sets the interval for MinMaxAvg
            :param interval: None=disable, "day"=day, "hour"=hour
            :return: None
            """
            allowed = [None, "day", "hour"]
            if interval in allowed:
                self.minmaxavg_interval = interval
            else:
                raise ValueError("Wrong parameter, has to be " + "or".join(allowed))

        def get_minmaxavg_interval(self):
            return self.minmaxavg_interval

        def set_line_color(self, color):
            self.line_color = color

        def get_line_color(self):
            return self.line_color

        def set_sensor(self, sensor):
            if not issubclass(type(sensor), BaseSensor):
                raise ValueError("sensor has to be a subclass of BaseSensor!")
            self.sensor = sensor

        def get_sensor(self):
            return self.sensor

        def get_axis(self):
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

        def __hash__(self):
            st = self.sensor.get_short_name + self.line_color + self.minmaxavg_interval
            return hash(st)

    def __init__(self):
        self.xtick_str = None
        self.xtick_pos = None
        self.figsize = (16, 9)
        self.dpi = 120
        self.axes = []  # axes[0] is ["label left", "label right"]
        self.data = None
        self.datalines = None  # dict, key: shortname of sensor, value: (x: np.array, y: np.array)
        self.sensoroptions = []
        self.start = None
        self.end = None
        self.title = None
        self.axislabels = None  # dict, key: for example "1b", value: label

    def add_sensoroption(self, option: CustomPlotSensorOptions):
        ha = hash(option)
        for op in self.sensoroptions:
            if hash(op) == option:
                return  # already in list
        self.sensoroptions.append(option)

    def get_sensoroptions(self):
        return self.sensoroptions

    def set_start(self, start: datetime.datetime):
        now = datetime.datetime.now()
        if start > now:
            raise ValueError("Start must be before now!")
        if self.end is not None and self.end < start:
            raise ValueError("Start must be before end!")
        self.start = start

    def get_start(self):
        return self.start

    def set_end(self, end: datetime.datetime):
        now = datetime.datetime.now()
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
        oneday = datetime.timedelta(days=1)
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
        for sensor in self.get_sensoroptions():
            color = sensor.get_line_color()
            if not color:
                sensor.set_line_color(standards.pop())
            elif color in standards:
                standards.remove(color)

    def split_date_to_lines(self):
        if self.datalines is not None:
            return  # Already splitted
        for sensoroption in self.sensoroptions:
            shortname = sensoroption.get_sensor().get_short_name()
            x = np.array([])
            y = np.array([])
            for day in self.data.data:
                if shortname in day.fields:
                    np.append(x, day.array[:, 0])
                    np.append(y, day.array[:, day.fields.index(shortname)])
            self.datalines[shortname] = (x, y)

    def prepare_axis_labels(self):
        if self.axislabels is not None:
            return
        self.axislabels = {}
        for sensoroption in self.sensoroptions:
            label = sensoroption.get_sensor().get_long_name() + \
                    " [" + sensoroption.get_sensor().get_unit() + "]"
            axis = sensoroption.get_axis()
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
        axes = filter(lambda x: x is not None, self.axes)

    def generate_xticks(self):
        if self.data is None:
            raise ValueError("Load data first!!")
        self.xtick_pos = []
        self.xtick_str = []
        for day in self.

    def create_plots(self):
        fig, subs = plt.subplots(nrows=len(self.axes), sharex="all", figsize=self.figsize, dpi=self.dpi)
        plt.xticks(self.xtick_pos, self.xtick_str, rotation=90)
        for i, subplt in enumerate(subs):
            labels = self.axes[i]
