# coding=utf-8
import time

from wetstat.hardware.sensors.real.light_sensor import LightSensor

ls = LightSensor()

x = False

while True:
    print("\r", " " * 80, end="")
    print(f"\rValue: {round(ls.measure(), 3)} lux, mode is {ls.mode} {' .' if x else '. '}", end="")
    x = not x
    time.sleep(0.5)
