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


def load_csv_for_range(folder: str, start: datetime.date, end: datetime.date) -> DataContainer:
    if start > end:
        raise ValueError("end must be after start!!!")

    container = DataContainer(list())
    while start <= end:
        container.data.append(
            load_csv_to_daydata(
                os.path.join(
                    folder,
                    get_filename_for_date(start)
                )
            )
        )
        start = start + datetime.timedelta(days=1)  # increase date
    return container


def get_data_folder():
    folder = os.path.realpath(os.path.dirname(__file__))
    path = os.path.join(folder, "datafolder")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file 'datafolder' in '{folder}' doesn't exist!")
    with open(path) as file:
        content = file.read().strip()
    return content


def save_range_to_csv(folder: str, container: DataContainer):
    for daydata in container.data:
        save_daydata_to_csv(daydata, folder)


def load_csv_to_daydata(filename: str, separator=";") -> DayData:
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


def save_daydata_to_csv(data: DayData, folder: str, separator=";"):
    filename = os.path.join(folder, data.date.strftime("day%jin%y.csv"))
    with open(filename, "w") as file:
        file.write(separator.join(data.fields))
        for record in data.array:
            file.write("\n")
            file.write(record[0].strftime("%H:%M"))
            for value in record[1:]:
                file.write(";" + str(value))


def get_filename_for_date(date: datetime.date) -> str:
    return date.strftime("day%jin%y.csv")


def save_values(folder: str, heads: list, data: list, timelabel: datetime.datetime):
    path = os.path.join(folder, get_filename_for_date(timelabel))
    with open(path, "r+") as f:
        firstline = f.readline()
        fileheads = firstline.split(";")
        col_indexes = []
        for h in heads:
            try:
                idx = fileheads.index(h)
                col_indexes.append(idx)
            except ValueError:  # h not in fileheads
                col_indexes.append(-1)
