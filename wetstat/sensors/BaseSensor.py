class BaseSensor:
    def __init__(self):
        raise RuntimeWarning("you should not instanciate this class directly!")

    def get_info(self):
        try:
            return {"long_name": self.get_long_name(),
                    "short_name": self.get_short_name(),
                    "color": self.get_display_color(),
                    "unit": self.get_unit()}
        except NameError:
            raise NotImplementedError("child class hasn't defined one of the info methods correctly!")
