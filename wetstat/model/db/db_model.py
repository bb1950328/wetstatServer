# coding=utf-8
import collections
import datetime
import time
from concurrent import futures
from dataclasses import dataclass
from typing import List, Union, Iterable, Dict, Collection, Optional

import numpy as np
from mysql import connector
from mysql.connector import MySQLConnection, IntegrityError
from mysql.connector.cursor import MySQLCursor

from wetstat.common import logger
from wetstat.model import util
# from wetstat.model.csvtools import DayData, DataContainer
from wetstat.model.db import db_const


@dataclass
class DbData(object):
    array: np.ndarray
    columns: List[str]


def create_connection() -> MySQLConnection:
    return connector.connect(database=db_const.DATABASE_NAME,
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
    cursor.execute("EXPLAIN " + db_const.DATA_DB_NAME)
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
    cursor.execute(f"ALTER TABLE {db_const.DATA_DB_NAME} ADD {col_name} FLOAT;")
    logger.log.info(f"Added column '{col_name}' in {db_const.DATABASE_NAME}.{db_const.DATA_DB_NAME}")
    if is_own_cursor:
        cursor.close()


def to_sql_str(value: object) -> str:
    if isinstance(value, datetime.datetime):
        return "'" + value.strftime(db_const.DATETIME_FORMAT) + "'"
    else:
        return str(value)


def insert_daydata(daydata, add_missing_columns=False, create_own_connection=False) -> None:
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
                # single insert because not all records have errors, so some require insert and some require update
                for record in values:
                    do_insert(connection, cursor, column_names, record)
            else:
                # only one record, we know that this record causes the problem
                values = values[0]
                timestamp = values[column_names.index(db_const.COL_NAME_TIME)]
                do_update(connection, cursor, timestamp, column_names, values)
        else:
            raise e


def do_update(connection, cursor, timestamp, column_names, values: Iterable[object]) -> None:
    sets = [f"{col}={val}" for col, val in zip(column_names, values)]
    final_command = f"UPDATE {db_const.DATA_DB_NAME} SET {', '.join(sets)} " \
                    f"WHERE {db_const.COL_NAME_TIME}={to_sql_str(timestamp)};"
    cursor.execute(final_command)
    connection.commit()


def insert_datacontainer(container, use_threads=False, add_missing_columns=True) -> None:
    if use_threads:
        ex = futures.ThreadPoolExecutor()
        for dd in container.data:
            ex.submit(insert_daydata, dd, add_missing_columns=add_missing_columns, create_own_connection=True)
        ex.shutdown()
    else:
        for dd in container.data:
            insert_daydata(dd, add_missing_columns=add_missing_columns)


def load_data_for_date_range(start: datetime.datetime, end: datetime.datetime) -> DbData:
    cur = None
    try:
        cur = conn.cursor()
        execute_select_range(start, end, cur)
        db_data = fetch_to_db_data(cur)
        return db_data
    finally:
        if cur:
            cur.close()


def execute_select_range(start, end, cursor, columns=None) -> None:
    """
    Executes the select statement on the given cursor.
    :return: None
    """
    if columns is None:
        column_list = "*"
    else:
        column_list = ", ".join(columns)
    util.validate_start_end(start, end)
    params = start.strftime(db_const.DATETIME_FORMAT), end.strftime(db_const.DATETIME_FORMAT)
    cursor.execute(f"SELECT {column_list} FROM {db_const.DATA_DB_NAME} WHERE"
                   f" {db_const.COL_NAME_TIME} BETWEEN %s AND %s", params)


def insert_record(timestamp: datetime.datetime, update_if_exists=False, **values):
    """
    example call: insert_record(time, Temp1=3, Light=5, update_if_exists=True)
    """
    cur = None
    try:
        cur = conn.cursor()
        cols = list(values.keys())
        cols.append(db_const.COL_NAME_TIME)
        vals = list(values.values())
        vals.append(to_sql_str(timestamp))
        do_insert(conn, cur, cols, vals, update_if_exists)
    finally:
        if cur:
            cur.close()


def fetch_to_db_data(cursor: MySQLCursor) -> DbData:
    return DbData(np.array(cursor.fetchall()), cursor.column_names)


def export_to_csv(start: datetime.datetime, end: datetime.datetime, path: str,
                  columns: Optional[Collection[str]] = None, delimiter=";", none_value: str = ""):
    start_ts = time.perf_counter()
    cur = None
    out = None
    try:
        cur = conn.cursor()
        execute_select_range(start, end, cur)
        if columns is None:
            columns = cur.column_names
            col_nums = range(len(columns))
        else:
            col_nums = []
            for df_col in columns:
                try:
                    col_nums.append(cur.column_names.index(df_col))
                except ValueError:
                    pass
        out = open(path, "w")
        out.write(delimiter.join([cur.column_names[n] for n in col_nums]) + "\n")

        def to_str(value: object) -> str:
            if value is None:
                return none_value
            if isinstance(value, datetime.datetime):
                return value.strftime(db_const.EXPORT_DATETIME_FORMAT)
            elif isinstance(value, float):
                return str(round(value, 3))
            else:
                return str(value)

        while True:
            db_row = cur.fetchone()
            if not db_row:
                break
            db_row = list(db_row)
            try:
                time_index = cur.column_names.index(db_const.COL_NAME_TIME)
                db_row[time_index] = db_row[time_index].isoformat()
            except ValueError:
                pass
            out.write(delimiter.join([to_str(db_row[n]) for n in col_nums]) + "\n")

        end = time.perf_counter()
        size = out.tell()
        secs = end - start_ts
        by_per_sec = size / secs
        logger.log.info(f"Exported {util.human_readable_size(size)} in {round(secs, 5)} seconds to '{path}'"
                        f"({util.human_readable_size(by_per_sec)}/s)")
    finally:
        if cur:
            cur.close()
        if out:
            out.close()


def find_nearest_record(timestamp: datetime.datetime):
    """
    :param timestamp: datetime.datetime
    :return: nearest record, to past if one record is as far as another record
    """
    time_str = to_sql_str(timestamp)
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM data WHERE Time >= {time_str} ORDER BY Time LIMIT 1;")
        res_future = cur.fetchone()
        future_cols = cur.column_names
        future_time_index = future_cols.index(db_const.COL_NAME_TIME)
        to_future = res_future[future_time_index] - timestamp

        cur.execute(f"SELECT * FROM data WHERE Time <= {time_str} ORDER BY Time DESC LIMIT 1;")
        res_past = cur.fetchone()
        past_cols = cur.column_names
        past_time_index = past_cols.index(db_const.COL_NAME_TIME)
        to_past = timestamp - res_past[past_time_index]
        if to_future < to_past:
            record, columns = res_future, future_cols
        else:
            record, columns = res_past, past_cols

        return record_to_dict(record, columns)

    finally:
        if cur:
            cur.close()


def get_value_sums(columns,
                   *,
                   start: datetime.datetime = None,
                   end: datetime.datetime = None,
                   duration: datetime.timedelta = None) -> Dict[str, float]:
    start, end, duration = util.calculate_missing_start_end_duration(end, start, duration)
    if not all(map(util.is_valid_sql_name, columns)):
        raise ValueError("At least one of the given column names is invalid!!!")
    col_list = (f"SUM({sn}) AS {sn}" for sn in columns)
    cur = None
    try:
        cur = conn.cursor()
        execute_select_range(start, end, cur, col_list)
        return record_to_dict(cur.fetchone(), cur.column_names, none_value=0)
    finally:
        if cur:
            cur.close()


def record_to_dict(record: Iterable, columns: Iterable[str], none_value=None):
    return {col: value if value is not None else none_value
            for col, value in zip(columns, record)}


def cleanup() -> None:
    conn.close()
    logger.log.debug("Database connection closed.")
