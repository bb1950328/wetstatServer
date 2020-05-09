# coding=utf-8
import threading
import time
from typing import List

from mysql import connector
from mysql.connector import MySQLConnection

from wetstat.model.db import db_const

MAX_CONNECTIONS = 16
_connections: List[MySQLConnection] = []
_used: List[bool] = []
_meta_lock = threading.Lock()


def find_conn() -> MySQLConnection:
    with _meta_lock:
        if all(_used) and len(_connections) < MAX_CONNECTIONS:
            conn = _new_connection()
            _connections.append(conn)
            conn.commit()
            return conn
    while True:
        with _meta_lock:
            for i, lo in enumerate(_used):
                if not lo:
                    _used[i] = True
                    conn = _connections[i]
                    conn.ping(reconnect=True, attempts=10, delay=1)
                    conn.commit()
                    return conn
        time.sleep(0.1)


def release_conn(conn: MySQLConnection) -> None:
    for i, co in enumerate(_connections):
        if co == conn:
            with _meta_lock:
                _used[i] = False
            return


def _new_connection() -> MySQLConnection:
    return connector.connect(database=db_const.DATABASE_NAME,
                             user="wetstat_user",
                             password="wetstat",
                             host="localhost",
                             port=3306,
                             buffered=True,
                             )


def cleanup():
    for co in _connections:
        co.close()
