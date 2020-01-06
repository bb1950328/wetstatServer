# coding=utf-8
import datetime
from typing import Union, List, Dict, Optional

from wetstat.model.db import db_model


class Patcher(object):
    DATA_FILE = r"C:\tmp\agrometeo-data3.csv"
    TIME_FORMAT = "%d.%m.%Y %H:%M"
    CSV_NULL_CHARS = "?x"

    class CSVIterator(object):
        def __init__(self, path: str, delimiter: str = ";") -> None:
            self.delimiter = delimiter
            self.f = open(path)
            self.headers = self._read_line_and_split(convert=False)
            self._current: Optional[Dict[str, Union[str, float, datetime]]] = None

        @property
        def current(self) -> Dict[str, Union[str, float, datetime.datetime]]:
            if self._current is None:
                self.next()
            return self._current

        def _read_line_and_split(self, convert: bool = True) \
                -> Union[List[Union[str, float, datetime.datetime]], List[str]]:
            line = self.f.readline().strip()
            splitted = line.split(self.delimiter)
            if not any(splitted):  # end of file or line like this: ;;;;
                return []
            return [Patcher.CSVIterator._try_to_convert(v) for v in splitted] if convert else splitted

        @staticmethod
        def _try_to_convert(value: str) -> Union[str, float, datetime.datetime]:
            try:
                return float(value)
            except ValueError:
                try:
                    return datetime.datetime.strptime(value, Patcher.TIME_FORMAT)
                except ValueError:
                    return value

        def next(self) -> bool:  # false if file is exhausted
            self._current = {head: value for head, value in zip(self.headers, self._read_line_and_split())
                             if str(value) not in Patcher.CSV_NULL_CHARS}
            return len(self._current) > 0

    class SQLIterator(object):
        def __init__(self) -> None:
            self._cursor = db_model.conn.cursor()
            self._current = None

        @property
        def current(self) -> dict:
            if self._current is None:
                self.next()
            return self._current

        def next(self) -> bool:
            if self._current is not None:
                mid_dt = self.current["Time"]
                self._cursor.execute(f"SELECT * FROM data WHERE Time > {db_model.to_sql_str(mid_dt)} "
                                     f"ORDER BY Time LIMIT 1")
            else:
                self._cursor.execute("SELECT * FROM data ORDER BY Time LIMIT 1")
            fetched = self._cursor.fetchone()
            if not fetched:
                return False
            self._current = {col: val for col, val in zip(self._cursor.column_names, fetched)}
            return len(self._current) > 0

    def __init__(self) -> None:
        self.cur = None
        self.sql = Patcher.SQLIterator()
        self.csv = Patcher.CSVIterator(Patcher.DATA_FILE)
        self.i_db = None
        self.i_csv = None

    def run(self) -> None:
        try:
            self.cur = db_model.conn.cursor()
            sql_at_end = not self.sql.next()
            executed = 0
            while self.csv.next():
                while self.sql.current["Time"] < self.csv.current["Time"] and not sql_at_end:
                    sql_at_end = not self.sql.next()
                # print(self.sql.current["Time"], self.csv.current["Time"], sql_at_end)
                if self.sql.current["Time"] == self.csv.current["Time"] and not sql_at_end:
                    # print("eq")
                    self.extend_current_sql()
                else:
                    self.insert_sql_from_csv()
                executed += 1
                if executed > 64:
                    db_model.conn.commit()
                    print("COMMIT")
                    executed = 0
        finally:
            db_model.conn.commit()
            self.cur.close()
            db_model.conn.close()

    def extend_current_sql(self) -> None:
        to_extend = []
        for sk, sv in self.sql.current.items():
            if sv is None and sk in self.csv.current.keys():
                to_extend.append(sk)
        dt = self.sql.current["Time"]
        if len(to_extend) > 0:
            sets = ", ".join([str(col) + "=" + str(self.csv.current[col]) for col in to_extend])
            query = f"UPDATE data SET {sets} WHERE Time={db_model.to_sql_str(dt)}"
            print(query)
            self.cur.execute(query)
        else:
            print("cannot extend ", dt)

    def insert_sql_from_csv(self) -> None:
        common_cols = tuple(set(self.csv.current.keys()) & set(self.sql.current.keys()))
        if common_cols == ("Time",) or "Time" not in common_cols:
            return
        cols = ", ".join(common_cols)
        values = ", ".join([db_model.to_sql_str(self.csv.current[k]) for k in common_cols])
        query = f"INSERT INTO data ({cols}) VALUES ({values});"
        print(query)
        self.cur.execute(query)


if __name__ == '__main__':
    pa = Patcher()
    pa.run()
    print("Finished.")
