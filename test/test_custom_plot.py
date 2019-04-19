import datetime
import os

import wetstat.sensors.TempSensor
from wetstat import models

cp = models.CustomPlot()

cp.set_start(datetime.datetime(2018, 7, 1))
cp.set_end(datetime.datetime(2018, 7, 31))

ts = wetstat.sensors.TempSensor.TempSensor(1)

so1 = models.CustomPlotSensorOptions(ts)
so1.set_axis("0b")
so1.set_minmaxavg_interval("hour")

so2 = models.CustomPlotSensorOptions(ts)
so2.set_axis("1a")
so2.set_minmaxavg_interval("day")

so3 = models.CustomPlotSensorOptions(ts)
so3.set_axis("2b")
so3.set_minmaxavg_interval("week")

so4 = models.CustomPlotSensorOptions(ts)
so4.set_axis("3a")
so4.set_minmaxavg_interval("month")

so5 = models.CustomPlotSensorOptions(ts)
so5.set_axis("4b")
so5.set_minmaxavg_interval("year")

so6 = models.CustomPlotSensorOptions(ts)
so6.set_axis("5a")

cp.add_sensoroption(so1)
cp.add_sensoroption(so2)
cp.add_sensoroption(so3)
cp.add_sensoroption(so4)
cp.add_sensoroption(so5)
cp.add_sensoroption(so6)

cp.set_legend_mode(1)

cp.filename = os.path.realpath(__file__ + ".svg")
cp.create_plots()
