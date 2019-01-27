import datetime
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np


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


@dataclass
class DayData:
    date: datetime.date
    array: np.array
    fields: list


class CSVTools:
    @staticmethod
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
            d = datetime.strptime(os.path.basename(filename).split(".")[0], "day%jin%y")
            fields = list(map(str.strip, file.readline().split(separator)))
            data = []
            for line in file:
                spl = line.split(separator)
                dt = datetime.strptime(spl[0], "%H:%M")
                dataline = [datetime.combine(d.date(), dt.time())]
                for value in spl[1:]:
                    try:
                        dataline.append(float(value))
                    except ValueError as e:
                        dataline.append(0.0)
                data.append(dataline)
        res = DayData(d, np.array(data), fields)
        return res

    @staticmethod
    def save_daydata_to_csv(data: DayData, folder: str, separator=";"):
        filename = os.path.join(folder, data.date.strftime("day%jin%y.csv"))
        with open(filename, "w") as file:
            file.write(separator.join(data.fields))
            for record in data.array:
                file.write("\n")
                file.write(record[0].strftime("%H:%M"))
                for value in record[1:]:
                    file.write(";" + str(value))
