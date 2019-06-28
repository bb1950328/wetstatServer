# coding=utf-8
import json
import socket
import threading
from typing import Dict, Union

from wetstat.service_manager.service_manager import COM_PORT, COMMAND_INFO, COMMAND_LIST

addr = ("localhost", COM_PORT)
lock = threading.Lock()


def run_command(command: str) -> str:
    with lock:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        sock.send(command.encode())
        return sock.recv(4096).decode()


def get_info() -> Dict[str, Dict[str, Union[str, bool, float]]]:
    return json.loads(run_command(COMMAND_INFO))


def get_list() -> list:
    return json.loads(run_command(COMMAND_LIST))
