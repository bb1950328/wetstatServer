import datetime

import wetstat.sensors.TempSensor
from wetstat import models

cp = models.CustomPlot()

cp.set_start(datetime.datetime(2018, 1, 1))
cp.set_end(datetime.datetime(2018, 1, 31))

ts = wetstat.sensors.TempSensor.TempSensor(1)
so = models.CustomPlot.CustomPlotSensorOptions(ts)
so.set_axis("1a")
cp.add_sensoroption(so)
cp.create_plots()
