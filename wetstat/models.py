import datetime
import os
from dataclasses import dataclass
import datetime

from matplotlib import rcParams

from wetstat import csvtools

import numpy as np
import matplotlib.pyplot as plt


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
                  linewidth=0.75):
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
    fig, ax1 = plt.subplots()
    plt.sca(ax1)
    plt.xticks(xtick_pos, xtick_str, rotation=rotation)
    ax1.xaxis.grid(True, linestyle="-")
    ax1.yaxis.grid(True, linestyle="-")
    ax1.set_ylabel(yaxis1label)
    ax2 = ax1.twinx()
    ax2.set_ylabel(yaxis2label)
    plt.title(title, pad=30)
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
    plt.savefig(r"C:\Users\dev\Desktop\testfig.svg")
    fig.show()
