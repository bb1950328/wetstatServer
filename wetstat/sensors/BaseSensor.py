# coding=utf-8
class BaseSensor:
    MINMAXAVG = "minmaxavg"
    SUM = "sum"
    MIN = "min"
    MAX = max

    def __init__(self):
        raise RuntimeWarning("you should not instantiate this class directly!")

    def get_info(self):
        try:
            return {"long_name": self.get_long_name(),
                    "short_name": self.get_short_name(),
                    "color": self.get_display_color(),
                    "unit": self.get_unit()}
        except NameError:
            raise NotImplementedError("child class hasn't defined one of the info methods correctly!")

    def get_long_name(self):
        raise NotImplementedError("child class hasn't defined get_long_name() correctly!")

    def get_short_name(self):
        raise NotImplementedError("child class hasn't defined get_short_name() correctly!")

    def get_display_color(self):
        raise NotImplementedError("child class hasn't defined get_display_color() correctly!")

    def get_unit(self):
        raise NotImplementedError("child class hasn't defined get_unit() correctly!")

    def get_compression_function(self):
        return self.MINMAXAVG
