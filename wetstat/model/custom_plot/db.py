# coding=utf-8
import datetime
import sqlite3
from typing import Tuple

from wetstat.common import config

conn = sqlite3.connect(config.get_database())


class CustomPlotDbRow:
    id: str
    path: str
    created: datetime.datetime
    title: str

    def encode(self) -> Tuple[str, str, datetime, str]:
        return self.id, self.path, self.created, self.title


def is_id_available(id_: str) -> bool:
    c = conn.cursor()
    c.execute("SELECT id FROM plots WHERE id=?", id_)
    return not c.fetchall()


def delete_row(id_: str):
    with conn:
        c = conn.cursor()
        c.execute("DELETE FROM plots WHERE id=?", id_)
