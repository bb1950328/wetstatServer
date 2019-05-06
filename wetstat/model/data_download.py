# coding=utf-8
from datetime import datetime
from typing import Optional

from wetstat.model import csvtools


class DataDownload:
    start: Optional[datetime]
    end: Optional[datetime]

    def __init__(self):
        self.start = None
        self.end = None

    def set_start(self, start: datetime):
        self.start = start

    def set_end(self, end: datetime):
        self.end = end

    def load_data(self):
        datacontainer = csvtools.load_csv_for_range()
