import os
import tempfile
from unittest import TestCase

from wetstat.models import CSVTools


class TestCSVTools(TestCase):
    def test_load_save_csv_daydata(self):
        tempdir = tempfile.gettempdir()
        resourcesdir = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            "resources")
        print(resourcesdir)
        res = CSVTools.load_csv_to_daydata(os.path.join(resourcesdir, "day123in18.txt"))
        self.assertEqual((3, 4), res.array.shape)
        self.assertEqual(['Time', 'Temp1', 'Temp2', 'Light'], res.fields)
        # TODO some more tests
        self.fail()
