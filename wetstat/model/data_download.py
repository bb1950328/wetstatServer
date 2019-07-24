# coding=utf-8
import os
import random
import shutil
from datetime import datetime, timedelta
from typing import Optional

from wetstat.common import config
from wetstat.model import csvtools


class DataDownload:
    col_selection: Optional[set]
    start: Optional[datetime]
    end: Optional[datetime]
    single_file: bool = True
    make_zip: bool = True  # ignored if single_file == False
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

    def make_single_file(self) -> str:
        csv_path = self.get_filepath() + ".csv"
        csvtools.save_datacontainer_to_single_csv(
            csvtools.load_csv_for_range(config.get_datafolder(),
                                        self.start,
                                        self.end),
            csv_path,
            self.col_selection,
        )
        return csv_path

    def make_single_file_zip(self) -> str:
        """
        :return: full path of zip
        """
        zip_path = self.get_filepath()
        shutil.make_archive(zip_path, "zip", root_dir=self.plotfolder, base_dir=self.file_id + ".csv")
        return self.get_filepath() + ".zip"

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
        if self.single_file:
            self.make_single_file()
            if self.make_zip:
                self.make_single_file_zip()
        else:
            folder = self.get_filepath()
            os.mkdir(folder)
            i = self.start.date()
            imax = self.end.date()
            oneday = timedelta(days=1)
            datafolder = config.get_datafolder()
            while i <= imax:
                f = os.path.join(datafolder, csvtools.get_filename_for_date(i))
                i += oneday
                shutil.copy(f, folder)
            shutil.make_archive(self.get_filepath(), "zip", folder)
            shutil.rmtree(folder)
        return self.get_filepath() + (".zip" if self.make_zip or (not self.single_file) else ".csv")
