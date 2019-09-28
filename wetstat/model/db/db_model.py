# coding=utf-8
import datetime
from concurrent import futures
from typing import List

from mysql import connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from wetstat.common import logger
from wetstat.model import util
from wetstat.model.csvtools import DayData, DataContainer
from wetstat.model.db import db_const


def create_connection() -> MySQLConnection:
    return connector.connect(database="wetstat",
                             user="root",
                             password="root",
                             host="localhost",
                             port=3306,
                             )


conn = create_connection()


def get_all_columns(cursor: MySQLCursor = None) -> List[str]:
    if not cursor:
        cursor = conn.cursor()
        is_own_cursor = True
    else:
        is_own_cursor = False
    cursor.execute("EXPLAIN data")
    exp = cursor.fetchall()
    if is_own_cursor:
        cursor.close()
    return [col[0] for col in exp]


def add_column(col_name: str, cursor: MySQLCursor = None):
    if not cursor:
        cursor = conn.cursor()
        is_own_cursor = True
    else:
        is_own_cursor = False
    if not util.is_valid_sql_name(col_name):
        raise ValueError(f"Invalid column name: '{col_name}'!!!!")
    cursor.execute(f"ALTER TABLE data ADD {col_name} FLOAT;")
    logger.log.info(f"Added column '{col_name}' in wetstat.data")
    if is_own_cursor:
        cursor.close()


def to_sql_str(value: object) -> str:
    if isinstance(value, datetime.datetime):
        return value.strftime(db_const.DATETIME_FORMAT)
    else:
        return str(value)


def insert_daydata(daydata: DayData, add_missing_columns=False, create_own_connection=False) -> None:
    if create_own_connection:
        connection = create_connection()
    else:
        connection = conn
    cur = None
    try:
        cur = connection.cursor()
        db_heads = get_all_columns(cur)
        dd_heads = daydata.fields
        missing = set(dd_heads) - set(db_heads)  # fields which are in dd_heads but not in db_heads
        if len(missing):
            if add_missing_columns:
                for m in missing:
                    add_column(m)
            else:
                raise ValueError(f"The following columns are missing in the table: {missing}")
        if not all(map(util.is_valid_sql_name, dd_heads)):
            raise ValueError("Invalid column name in DayData!!!")
        columns = ", ".join(dd_heads)
        statement = f"INSERT INTO data ({columns}) VALUES "
        values = []
        for record in daydata.array:
            values.append("(" + ", ".join(map(to_sql_str, record)) + ")")
        final_command = statement + ", ".join(values) + ";"
        cur.execute(final_command)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e

    finally:
        if cur:
            cur.close()
        if create_own_connection:
            connection.close()


def insert_datacontainer(container: DataContainer, use_threads=False, add_missing_columns=True) -> None:
    if use_threads:
        ex = futures.ThreadPoolExecutor()
        for dd in container.data:
            ex.submit(insert_daydata, dd, add_missing_columns=add_missing_columns, create_own_connection=True)
        ex.shutdown()
    else:
        for dd in container.data:
            insert_daydata(dd, add_missing_columns=add_missing_columns)


def cleanup() -> None:
    conn.close()
    logger.log.debug("Database connection closed.")
