import datetime
import os

import wetstat.sensors.TempSensor
from wetstat import models

cp = models.CustomPlot()

cp.set_start(datetime.datetime(2018, 1, 1))
cp.set_end(datetime.datetime(2018, 1, 31))

ts = wetstat.sensors.TempSensor.TempSensor(1)
so = models.CustomPlot.CustomPlotSensorOptions(ts)
so.set_axis("1a")
cp.add_sensoroption(so)
so2 = models.CustomPlot.CustomPlotSensorOptions(ts)
so2.set_axis("2b")
cp.add_sensoroption(so2)
cp.filename = os.path.realpath(__file__ + ".png")
cp.create_plots()
