# coding=utf-8
import datetime
import pprint

from wetstat.model import csvtools

start = datetime.datetime(2018, 1, 2, 12, 0)
duration = datetime.timedelta(days=3)
res = csvtools.get_value_sums(start=start, duration=duration)
pprint.pprint(res)
