import datetime
import os

import wetstat.sensors.TempSensor
from wetstat import models

cp = models.CustomPlot()

cp.set_start(datetime.datetime(2018, 6, 1))
cp.set_end(datetime.datetime(2018, 7, 31))

ts = wetstat.sensors.TempSensor.TempSensor(1)

so = models.CustomPlot.CustomPlotSensorOptions(ts)
so.set_axis("0a")
so.set_minmaxavg_interval("day")
so2 = models.CustomPlot.CustomPlotSensorOptions(ts)
so2.set_axis("1b")
so2.set_minmaxavg_interval("hour")
so3 = models.CustomPlot.CustomPlotSensorOptions(ts)
so3.set_axis("2a")

cp.add_sensoroption(so)
cp.add_sensoroption(so2)
cp.add_sensoroption(so3)
cp.filename = os.path.realpath(__file__ + ".png")
cp.create_plots()
