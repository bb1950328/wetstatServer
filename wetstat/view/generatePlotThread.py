# coding=utf-8
import threading

from wetstat.model.custom_plot.custom_plot import CustomPlot


class GeneratePlotThread(threading.Thread):
    def __init__(self, custom_plot: CustomPlot):
        super().__init__()
        self.cp = custom_plot

    def run(self) -> None:
        self.cp.create_plots()
