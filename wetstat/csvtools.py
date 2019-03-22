import datetime
import os

import numpy as np
from dataclasses import dataclass

from wetstat import config


@dataclass
class DayData:
    date: datetime.date
    array: np.array
    fields: list


@dataclass
class DataContainer:
    data: list


def load_csv_for_range(folder: str, start: datetime.date, end: datetime.date, ignore_missing=False) -> DataContainer:
    if start > end:
        raise ValueError("end must be after start!!!")

    container = DataContainer(list())
    while start <= end:
        filename = os.path.join(folder, get_filename_for_date(start))
        if not os.path.isfile(filename):
            if ignore_missing:
                continue
            else:
                raise FileNotFoundError("File not found: " + filename +
                                        "You can set argument ignore_missing to True to ignore this.")
        container.data.append(load_csv_to_daydata(filename))
        start = start + datetime.timedelta(days=1)  # increase date
    return container


def get_data_folder():
    return config.get_datafolder()


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
                    if value == "":
                        dataline.append(None)
                    else:
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
    """
    :param folder: folder of the csv's
    :param heads: list of the heads
    :param data: list of the values, same length as heads
    :param timelabel: timestamp of the values
    :return:
    """
    path = os.path.join(folder, get_filename_for_date(timelabel))
    if heads[0].lower() != "time":
        heads.insert(0, "Time")
    if not os.path.isfile(path):
        f = open(path, "w")
        f.write(";".join(heads))
        f.close()
    with open(path, "r+") as f:
        firstline = f.readline().strip()
        fileheads = firstline.split(";")
        col_indexes = []  # for every element in heads, which column is it in the file (start at 0)
        for h in heads:
            try:
                idx = fileheads.index(h)
                col_indexes.append(idx)
            except ValueError:  # h not in fileheads
                col_indexes.append(-1)
        real_cols = heads
        if -1 in col_indexes:  # new columns
            f.seek(0)
            oldlines = f.readlines()
            col = len(fileheads)
            new_heads = 0
            for i, head in enumerate(heads):
                if col_indexes[i] == -1:  # no column for this head
                    fileheads.append(head)
                    col_indexes[i] = col
                    col += 1
                    new_heads += 1
            oldlines[0] = ";".join(fileheads) + "\n"
            toadd = ";" * new_heads
            for i in range(1, len(oldlines)):
                oldlines[i] = oldlines[i].strip() + toadd + "\n"
            oldlines[-1] = oldlines[-1].strip()  # remove newline from last line
            f.seek(0)
            f.writelines(oldlines)
            real_cols = oldlines[0].split(";")
        f.seek(0, 2)  # move cursor to the end

        output = [""] * len(fileheads)
        output[0] = timelabel.strftime("%H:%M")
        for i, val in enumerate(data):
            output[col_indexes[i + 1]] = val
        f.write("\n")
        output = [str(n) for n in output]
        f.write(";".join(output))
