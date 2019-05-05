# coding=utf-8
import threading
from typing import Dict, List, Optional


class MessageContainer:
    def __init__(self):
        self._messages: Dict[str, List[str]] = {}
        self.messages_lock = threading.Lock()
        self.messages_lock_reversed = threading.Lock()

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
