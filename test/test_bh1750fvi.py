# coding=utf-8
import time

from wetstat.hardware.sensors.light_sensor import LightSensor

ls = LightSensor()

while True:
    print(f"\rValue: {ls.measure()} lux, mode is {ls.mode}", end="")
    time.sleep(0.5)
