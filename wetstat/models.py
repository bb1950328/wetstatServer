import datetime
import os

import matplotlib.pyplot as plt
import mpld3
import numpy as np

from wetstat import csvtools, config


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
