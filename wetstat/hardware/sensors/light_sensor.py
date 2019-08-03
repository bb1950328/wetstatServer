# coding=utf-8
from wetstat.hardware.sensors.base_sensor import BaseSensor
from wetstat.hardware.sensors.bh1750fvi import BH1750FVI, Const

DARK_THRESHOLD = 100
LIGHT_THRESHOLD = 40_000
DARK = "DARK"
NORMAL = "NORMAL"
LIGHT = "LIGHT"


class LightSensor(BaseSensor):

    def __init__(self) -> None:
        super().__init__()
        self.bh1750 = BH1750FVI()
        if not self.bh1750.dry_mode:
            self.bh1750.set_mode(Const.Opecode.Continious.H_RES)
        self.mode = NORMAL

    def get_long_name(self) -> str:
        return "Licht"

    def get_short_name(self) -> str:
        return "Light"

    def get_display_color(self) -> str:
        return "#228b22"

    def get_unit(self) -> str:
        return "Lux"

    def change_mode(self, new_mode):
        if self.mode == new_mode:
            return
        if new_mode == DARK:
            self.bh1750.set_mode(Const.Opecode.Continious.H2_RES)
            self.bh1750.set_mtreg(Const.MTreg.MT_MAX)
        else:
            if self.mode == DARK:
                self.bh1750.set_mode(Const.Opecode.Continious.H_RES)
            if new_mode == NORMAL:
                self.bh1750.set_mtreg(Const.MTreg.MT_DEFAULT)
            else:  # new_mode == LIGHT
                self.bh1750.set_mtreg(Const.MTreg.MT_MIN)
        self.mode = new_mode

    def measure(self, check_mode=True) -> float:
        value = self.bh1750.get_result()
        if check_mode:
            if value < DARK_THRESHOLD and self.mode != DARK:
                self.change_mode(DARK)
                return self.measure(check_mode=False)
            elif value > LIGHT_THRESHOLD and self.mode != LIGHT:
                self.change_mode(LIGHT)
                return self.measure(check_mode=False)
            elif DARK_THRESHOLD <= value <= LIGHT_THRESHOLD and self.mode != NORMAL:
                self.change_mode(LIGHT)
                return self.measure(check_mode=False)
        return value
