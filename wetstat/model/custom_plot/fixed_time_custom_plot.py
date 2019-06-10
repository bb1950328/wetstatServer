# coding=utf-8
import datetime

from wetstat.common.config import get_date
from wetstat.model.custom_plot.custom_plot import CustomPlot


class FixedTimeCustomPlot(CustomPlot):
    def __init__(self, length: int):
        """
        :param length: in days
        """
        super().__init__()
        today = get_date()
        before7days = today - datetime.timedelta(days=length)
        self.set_start(before7days)
        self.set_end(today)
        self.set_title(f"Letzte {length} Tage")
