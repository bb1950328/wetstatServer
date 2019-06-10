# coding=utf-8
import threading
from typing import Dict, List, Optional, Union


class MessageContainer:
    def __init__(self):
        self.PPS_DEFAULT_VALUE: int = 2
        self._messages: Dict[str, List[str]] = {}
        self.messages_lock = threading.Lock()
        self.pps_lock = threading.Lock()
        self._pps: Dict[str, Union[int, float]] = {}

    def add_message(self, plot_id: str, messge: str) -> None:
        with self.messages_lock:
            if plot_id not in self._messages.keys():
                self._messages[plot_id] = []
            self._messages[plot_id].append(messge)

    def get_messages(self, plot_id: str) -> Optional[List[str]]:
        with self.messages_lock:
            try:
                return self._messages[plot_id]
            except KeyError:
                return None

    def set_percent_per_second(self, plot_id: str, pps: Union[int, float]):
        with self.pps_lock:
            self._pps[plot_id] = pps

    def get_percent_per_second(self, plot_id: str) -> Union[int, float]:
        with self.pps_lock:
            try:
                return self._pps[plot_id]
            except KeyError:
                return self.PPS_DEFAULT_VALUE
