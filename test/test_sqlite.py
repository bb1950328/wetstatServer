# coding=utf-8

"""

"""

import sqlite3

from wetstat.common import config

db_path = config.get_sqlite_database()

conn = None
try:
    conn = sqlite3.connect(db_path)

finally:
    if conn:
        conn.close()
