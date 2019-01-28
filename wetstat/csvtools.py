import datetime
import os

import numpy as np
from dataclasses import dataclass


@dataclass
class DayData:
    date: datetime.date
    array: np.array
    fields: list


@dataclass
class DataContainer:
    data: list


def load_csv_for_range(self, start: datetime.date, end: datetime.date) -> DataContainer:
    container = DataContainer(list())
    while start <= end:
        container.data.append(
            self.load_csv_to_daydata(
                self.get_filename_for_date(start)
            )
        )
        start.replace(day=start.day + 1)  # increase date
    return container


def load_csv_to_daydata(self, filename: str, separator=";") -> DayData:
    """
    dayXXXinXX.csv
    Time;Sensor1;Sensor2;Sensor3
    Time is in format HH:MM
    :param filename:
    :param separator:
    :return: DayData
    """
    with open(filename, "r") as file:
        d = datetime.datetime.strptime(os.path.basename(filename).split(".")[0], "day%jin%y")
        fields = list(map(str.strip, file.readline().split(separator)))
        data = []
        for line in file:
            spl = line.split(separator)
            dt = datetime.datetime.strptime(spl[0], "%H:%M")
            dataline = [datetime.datetime.combine(d.date(), dt.time())]
            for value in spl[1:]:
                try:
                    dataline.append(float(value))
                except ValueError as e:
                    dataline.append(0.0)
            data.append(dataline)
    res = DayData(d, np.array(data), fields)
    return res


def save_daydata_to_csv(self, data: DayData, folder: str, separator=";"):
    filename = os.path.join(folder, data.date.strftime("day%jin%y.csv"))
    with open(filename, "w") as file:
        file.write(separator.join(data.fields))
        for record in data.array:
            file.write("\n")
            file.write(record[0].strftime("%H:%M"))
            for value in record[1:]:
                file.write(";" + str(value))


def get_filename_for_date(self, date: datetime.date) -> str:
    return date.strftime("day%jin%y.csv")
