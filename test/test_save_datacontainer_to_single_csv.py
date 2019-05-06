# coding=utf-8
from datetime import timedelta

from wetstat.common import config
from wetstat.model import csvtools

end = config.get_date()
start = end - timedelta(days=7)

csvtools.save_datacontainer_to_single_csv(
    csvtools.load_csv_for_range(
        config.get_datafolder(),
        start,
        end),
    __file__ + "_out.csv"
)
