# coding=utf-8
import os
import random
import shutil
from datetime import datetime
from typing import Optional

from wetstat.common import config
from wetstat.model.db import db_model


class DataDownload(object):
    col_selection: Optional[set]
    start: Optional[datetime]
    end: Optional[datetime]
    make_zip: bool = True
    file_id: str

    def __init__(self) -> None:
        self.plotfolder = os.path.join(config.get_staticfolder(), "plot")
        self.file_id = hex(random.randint(0x1000000000000, 0xfffffffffffff))[2:]
        self.start = None
        self.end = None
        self.col_selection = None

    def set_col_selection(self, selection: set):
        self.col_selection = selection

    def set_start(self, start: datetime):
        self.start = start

    def set_end(self, end: datetime):
        self.end = end

    def get_filepath(self) -> str:
        """
        :return: for example C:\\wetstat\\static\\plot\\1ace1f7045133
        """
        zip_path = os.path.join(self.plotfolder, self.file_id)
        return zip_path

    def prepare_download(self) -> str:
        """
        :return: the file path ready for download
        """
        csv_path = self.get_filepath() + ".csv"
        db_model.export_to_csv(self.start, self.end, csv_path, columns=self.col_selection)
        if self.make_zip:
            shutil.make_archive(self.get_filepath(), "zip", root_dir=self.plotfolder, base_dir=self.file_id + ".csv")
        return self.get_filepath() + (".zip" if self.make_zip else ".csv")
