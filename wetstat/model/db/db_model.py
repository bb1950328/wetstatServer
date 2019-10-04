# coding=utf-8
import collections
import datetime
from concurrent import futures
from dataclasses import dataclass
from typing import List, Tuple, Union, Iterable

from mysql import connector
from mysql.connector import MySQLConnection, IntegrityError
from mysql.connector.cursor import MySQLCursor

from wetstat.common import logger
from wetstat.model import util
from wetstat.model.csvtools import DayData, DataContainer
from wetstat.model.db import db_const


@dataclass
class DbData(object):
    array: List[Tuple[Union[datetime.datetime, float]]]
    columns: List[str]


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
        return "'" + value.strftime(db_const.DATETIME_FORMAT) + "'"
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
        do_insert(connection, cur, dd_heads, daydata.array)
    except Exception as e:
        connection.rollback()
        raise e

    finally:
        if cur:
            cur.close()
        if create_own_connection:
            connection.close()


def do_insert(connection, cursor, column_names, values: Union[Iterable[object], Iterable[Iterable[object]]],
              update_if_exists=False):
    columns = ", ".join(column_names)
    statement = f"INSERT INTO data ({columns}) VALUES "
    records = []
    is_multi_insert = True
    if not isinstance(values[0], collections.Iterable):
        is_multi_insert = False
        values = (values,)
    for record in values:
        records.append("(" + ", ".join(map(to_sql_str, record)) + ")")
    final_command = statement + ", ".join(records) + ";"
    try:
        cursor.execute(final_command)
        connection.commit()
    except IntegrityError as e:
        if "Duplicate entry" in e.msg and update_if_exists:
            if is_multi_insert:
                # single insert because only one of many records has errors
                for record in values:
                    do_insert(connection, cursor, column_names, record)
            else:
                # only one record, we know that this record causes the problem
                values = values[0]
                timestamp = values[column_names.index("Time")]
                do_update(connection, cursor, timestamp, column_names, values)
        else:
            raise e


def do_update(connection, cursor, timestamp, column_names, values: Iterable[object]) -> None:
    sets = [f"{col}={val}" for col, val in zip(column_names, values)]
    final_command = f"UPDATE data SET {', '.join(sets)} WHERE Time={to_sql_str(timestamp)};"
    cursor.execute(final_command)
    connection.commit()


def insert_datacontainer(container: DataContainer, use_threads=False, add_missing_columns=True) -> None:
    if use_threads:
        ex = futures.ThreadPoolExecutor()
        for dd in container.data:
            ex.submit(insert_daydata, dd, add_missing_columns=add_missing_columns, create_own_connection=True)
        ex.shutdown()
    else:
        for dd in container.data:
            insert_daydata(dd, add_missing_columns=add_missing_columns)


def load_data_for_date_range(start: datetime.datetime, end: datetime.datetime) -> DbData:
    util.validate_start_end(start, end)
    cur = None
    try:
        cur = conn.cursor()
        params = start.strftime(db_const.DATETIME_FORMAT), end.strftime(db_const.DATETIME_FORMAT)
        cur.execute("SELECT * FROM data WHERE Time BETWEEN %s AND %s", params)
        db_data = fetch_to_db_data(cur)
        return db_data
    finally:
        if cur:
            cur.close()


def insert_record(timestamp: datetime.datetime, **values):
    """
    example call: insert_record(time, Temp1=3, Light=5)
    """
    cur = None
    try:
        cur = conn.cursor()
        cols = list(values.keys())
        cols.append("Time")
        vals = list(values.values())
        vals.append(to_sql_str(timestamp))
        do_insert(conn, cur, cols, vals)
    finally:
        if cur:
            cur.close()


def fetch_to_db_data(cursor: MySQLCursor) -> DbData:
    return DbData(cursor.fetchall(), cursor.column_names)


def cleanup() -> None:
    conn.close()
    logger.log.debug("Database connection closed.")
