# coding=utf-8
import datetime

from wetstat import csvtools

timestamp = datetime.datetime(2018, 5, 3, 0, 0)
timestamp = timestamp.replace(minute=3)

csvtools.save_values("C:\\tmp\\", ["Temp1", "Temp2", "Baro"], [12.5, 12.1, 1002.4], timestamp)
