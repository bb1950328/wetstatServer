# coding=utf-8
import wetstat.model.csvtools as csvtools
import wetstat.model.models as models
import datetime

dc = csvtools.load_csv_for_range(r"C:\Users\dev\PycharmProjects\wetstatServer\data",
                                 datetime.date(2014, 1, 1),
                                 datetime.date(2014, 12, 31))

models.generate_plot(dc, 20, useaxis=[1, 0, 2],
                     make_minmaxavg=[True, False, True],
                     dateformat="%d.%m.%y",
                     figsize=(32, 8))
