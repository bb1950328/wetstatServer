# coding=utf-8
import datetime
import os
import tempfile
from unittest import TestCase

from wetstat import csvtools


def get_dirs():
    """
    :return: (resources_folder, temp_folder)
    """
    tempdir = tempfile.gettempdir()
    resourcesdir = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ),
        "resources")
    return resourcesdir, tempdir


class TestCSVTools(TestCase):
    def test_load_save_csv_daydata(self):
        resourcesdir, tempdir = get_dirs()
        res = csvtools.load_csv_to_daydata(os.path.join(resourcesdir, "day123in18.csv"))
        self.assertEqual((3, 4), res.array.shape)
        self.assertEqual(['Time', 'Temp1', 'Temp2', 'Light'], res.fields)
        self.assertEqual(datetime.datetime(2018, 5, 3, 0, 0), res.date)

        csvtools.save_daydata_to_csv(res, tempdir)
        afile = open(os.path.join(resourcesdir, "day123in18.csv"))
        bfile = open(os.path.join(tempdir, "day123in18.csv"))
        self.assertEqual(afile.read(),
                         bfile.read())
        afile.close()
        bfile.close()
