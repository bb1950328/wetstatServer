# coding=utf-8
import json
import socket
import threading
from typing import Dict, Union, Optional

from wetstat.service_manager.service_manager import COM_PORT, COMMAND_INFO, COMMAND_LIST

addr = ("localhost", COM_PORT)
lock = threading.Lock()


def run_command(command: str) -> str:
    with lock:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            sock.send(command.encode())
            sock.settimeout(5)
            return sock.recv(4096).decode()
        except ConnectionRefusedError:
            return ""
        except ConnectionError:
            return ""


def get_info() -> Optional[Dict[str, Dict[str, Union[str, bool, float]]]]:
    response = run_command(COMMAND_INFO)
    if not response:
        return None
    else:
        return json.loads(response)


def get_list() -> list:
    return json.loads(run_command(COMMAND_LIST))
