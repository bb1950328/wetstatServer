# coding=utf-8
import datetime
import random
import time
from concurrent import futures

from wetstat.hardware.sensors import counter_service

counter_service.COM_PORT = random.randint(30_000, 65_000)
counter_service.RES_PORT = counter_service.COM_PORT + 1
print("Command port: ", counter_service.COM_PORT)
print("Response port:", counter_service.RES_PORT)

PIN = 4  # BCM

value = 0


def run_counter_server() -> None:
    ex = futures.ThreadPoolExecutor()
    server = counter_service.CounterServiceServer()
    ex.submit(counter_service.CounterServiceServer.run_server, server)


def initialize_counter() -> None:
    response = counter_service.send_command(f"start {PIN}")
    print("[response='", response, "]", sep="", end="")


def refresh_value() -> None:
    global value
    command = f"get {PIN}"
    response = counter_service.send_command(f"get {PIN}")
    if not response.isnumeric():
        print("\r[" + datetime.datetime.now().isoformat() + "]", command, "->", response)
    else:
        value += int(response)


print("Starting counter server...", end="")
run_counter_server()
print(" done")
time.sleep(0.25)
print(f"Initializing counter for pin {PIN}...", end="")
initialize_counter()
print(" done")
time.sleep(0.25)
while True:
    refresh_value()
    mm = value * rain_sensor.MM_PER_BUCKET
    print(f"\rCount of pin {PIN}: {value}", end="")
    time.sleep(1)
