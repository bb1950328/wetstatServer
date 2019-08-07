# coding=utf-8
import time
from concurrent import futures

from wetstat.hardware.sensors import counter_service

PIN = 7  # BCM

value = 0


def run_counter_server() -> None:
    ex = futures.ThreadPoolExecutor()
    server = counter_service.CounterServiceServer()
    ex.submit(counter_service.CounterServiceServer.run_server, server)


def initialize_counter() -> None:
    print("response=", counter_service.send_command(f"start {PIN}"), end="")


def refresh_value() -> None:
    global value
    response = counter_service.send_command(f"get {PIN}")
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
    print(f"\rCount of pin {PIN}: {value}", end="")
    time.sleep(1)
