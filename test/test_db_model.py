# coding=utf-8
import datetime
import os
import tempfile
import time

from wetstat.common import config
from wetstat.model import csvtools
from wetstat.model.db import db_model


def insert_all_data() -> None:
    print("loading data...")
    container = csvtools.load_csv_for_range(config.get_datafolder(),
                                            datetime.date(2000, 1, 1), datetime.date(2019, 9, 28),
                                            ignore_missing=True)
    print("inserting data...")
    start = time.perf_counter()
    db_model.insert_datacontainer(container, use_threads=True)
    end = time.perf_counter()
    print(f"inserting finished in {end - start} seconds.")


def load1() -> None:
    start = datetime.datetime(2015, 1, 1)
    end = datetime.datetime(2015, 1, 2)
    data = db_model.load_data_for_date_range(start, end)
    print("finished")


def insert1() -> None:
    dt = datetime.datetime(2020, 1, 1)
    vs = {"Temp1": 123,
          "Light": 54321,
          }
    db_model.insert_record(dt, **vs, update_if_exists=True)


def test_export() -> None:
    start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime(2018, 12, 31)
    path = os.path.join(tempfile.gettempdir(), "test_db_model.csv")
    db_model.export_to_csv(start, end, path)


if __name__ == "__main__":
    try:
        # insert_all_data()
        # load1()
        # insert1()
        test_export()
    finally:
        db_model.cleanup()
