# coding=utf-8
import datetime
import json
import socket
import threading
import time
from concurrent import futures
from typing import Dict, Union, Optional

from wetstat.common import logger, config
from wetstat.service_manager import service

COM_PORT = 51_112
COMMAND_INFO = "info"
COMMAND_LIST = "list"
COMMAND_START = "start"
COMMAND_RESTART = "restart"
COMMAND_STOP = "stop"


class ServiceManager:
    socket: Optional[socket.socket]
    last_crash: Dict[str, datetime.datetime]
    services: Dict[str, service.BaseService]

    def __init__(self) -> None:
        self.services = {}
        self.submitted = {}
        self.last_crash = {}
        self.executor = futures.ThreadPoolExecutor()
        self.socket = None
        self.submitted_lock = threading.Lock()

    def update_service(self, name: str, service: service.BaseService) -> None:
        self.services[name] = service

    def remove_service(self, name: str) -> None:
        self.stop_service(name)
        del self.services[name]

    def stop_service(self, name: str) -> None:
        with self.submitted_lock:
            if self.services[name].stop():
                del self.submitted[name]
                return
            if self.submitted[name].cancel():
                del self.submitted[name]
            else:
                raise InterruptedError(f"stopping {name} failed.")

    def start_service(self, name: str) -> None:
        with self.submitted_lock:
            self.submitted[name] = self.executor.submit(self.services[name].run)

    def restart_service(self, name: str) -> None:
        self.stop_service(name)
        self.start_service(name)

    def watchdog(self, blocking=False) -> None:
        if not blocking:
            self.executor.submit(ServiceManager.watchdog, self, blocking=True)
            return
        while True:
            # futures.wait(self.submitted.values(), return_when=futures.FIRST_COMPLETED)
            # print("FIRST_EXCEPTION")
            time.sleep(1)
            with self.submitted_lock:
                for name, sub in self.submitted.items():
                    if not sub.running():
                        logger.log.warning(f"service \"{name}\" crashed.")
                        self.last_crash[name] = datetime.datetime.now()
                        if self.services[name].is_restart_after_crash():
                            logger.log.info(f"restarted service \"{name}\" after crash.")
                            self.start_service(name)
                        break

    def get_info(self) -> Dict[str, Dict[str, Union[str, bool, float]]]:
        data = {}
        for sens_name, sens_obj in self.services.items():
            lc = self.last_crash.get(sens_name)
            with self.submitted_lock:
                sens_data = {"name": sens_name,
                             "running": sens_name in self.submitted and self.submitted[sens_name].running(),
                             "last_crash": lc.timestamp() if lc is not None else None
                             }
            data[sens_name] = sens_data
        return data

    def run_server(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind(("", COM_PORT))
            self.socket.listen(3)
            while True:
                com, addr = self.socket.accept()
                data = True
                while data:
                    data = com.recv(1024).decode()
                    if data:
                        res = self.execute_command(data)
                        if not res.startswith("ERROR:"):
                            logger.log.info(f"Host {addr} sent command \"{data}\" to ServiceManager")
                        com.send(res.encode())
                com.close()
        finally:
            self.socket.close()

    def execute_command(self, data: str) -> str:
        data = data
        arg = data.split(" ")
        arg[0] = arg[0].lower()
        try:
            if arg[0] == COMMAND_INFO:
                return json.dumps(self.get_info())
            if arg[0] == COMMAND_LIST:
                return json.dumps(list(self.services.keys()))
            if arg[0] == COMMAND_START:
                self.start_service(arg[1])
                return "OK"
            if arg[0] == COMMAND_RESTART:
                self.restart_service(arg[1])
                return "OK"
            if arg[0] == COMMAND_STOP:
                self.stop_service(arg[1])
                return "OK"
        except KeyError:
            return "ERROR: service name wrong!"
        except InterruptedError as e:
            return f"ERROR: internal error during command execution ({e.args})"
        return "ERROR: unknown command"


if __name__ == '__main__':
    manager = ServiceManager()
    manager.update_service("apache", service.ApacheServerService())
    manager.update_service("sensors", service.SensorService())
    manager.update_service("counter", service.CounterService())
    manager.update_service("plot_cleanup", service.PlotCleanupService())
    manager.update_service("log_cleanup", service.LogCleanupService())
    manager.update_service("shutdown_button", service.ShutdownButtonService())

    if config.on_pi():
        manager.start_service("apache")
    manager.start_service("sensors")
    manager.start_service("counter")
    manager.start_service("plot_cleanup")
    manager.start_service("log_cleanup")
    manager.start_service("shutdown_button")

    manager.watchdog()
    try:
        manager.run_server()
    except:
        logger.log.exception("Exception while starting server")
