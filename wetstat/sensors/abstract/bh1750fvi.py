# coding=utf-8
import time

try:
    import smbus2
except:
    pass

from wetstat.model import util


class Const:
    ADDRESS = 0x23
    BUS_NR = 1

    class Opecode:
        POWER_OFF = 0b0000_0000
        POWER_ON = 0b0000_0001
        RESET = 0b0000_0111

        class Continious:
            L_RES = 0b0001_0000
            H_RES = 0b0001_0001
            H2_RES = 0b0001_0011
            ALL = (L_RES, H_RES, H2_RES)

        class OneTime:
            L_RES = 0b0010_0000
            H_RES = 0b0010_0001
            H2_RES = 0b0010_0011
            ALL = (L_RES, H_RES, H2_RES)

        ALL = (POWER_OFF, POWER_ON, RESET, *Continious.ALL, *OneTime.ALL)

        @staticmethod
        def is_L_RES(opecode: int) -> bool:
            return opecode == Const.Opecode.Continious.L_RES or opecode == Const.Opecode.OneTime.L_RES

        @staticmethod
        def is_H_RES(opecode: int) -> bool:
            return opecode == Const.Opecode.Continious.H_RES or opecode == Const.Opecode.OneTime.H_RES

        @staticmethod
        def is_H2_RES(opecode: int) -> bool:
            return opecode == Const.Opecode.Continious.H2_RES or opecode == Const.Opecode.OneTime.H2_RES

    class MeasureTime:
        # as milliseconds
        L_RES = 16
        H_RES = 120
        H2_RES = 120

        @staticmethod
        def get_for_opecode(mode: int) -> int:
            if Const.Opecode.is_L_RES(mode):
                return Const.MeasureTime.L_RES
            elif Const.Opecode.is_H_RES(mode):
                return Const.MeasureTime.H_RES
            else:
                return Const.MeasureTime.H2_RES

    class MTreg:
        MT_MIN = 31
        MT_DEFAULT = 69
        MT_MAX = 254
        CHANGE_HIGH = 0b01000_000
        CHANGE_LOW = 0b011_00000


class BH1750FVI:
    # datasheet: http://www.elechouse.com/elechouse/images/product/Digital%20light%20Sensor/bh1750fvi-e.pdf
    def __init__(self) -> None:
        try:
            self.bus = smbus2.SMBus(Const.BUS_NR)
            self.mode = Const.Opecode.POWER_OFF
            self.first_valid = util.get_time_ms()
            self.mtreg = Const.MTreg.MT_DEFAULT
            self.dry_mode = False
        except (PermissionError, NameError):
            self.dry_mode = True

    def wait_until_valid(self) -> None:
        diff = self.first_valid - util.get_time_ms()
        if diff > 0:
            time.sleep(diff / 1000)

    def check_not_dry_mode(self) -> None:
        if self.dry_mode:
            raise ConnectionError("This instance is in dry mode because of an permission problem while opening I2C bus")

    def set_mode(self, opecode: int) -> None:
        self.check_not_dry_mode()
        if opecode not in Const.Opecode.ALL:
            raise ValueError("opecode not valid!!!")
        if opecode == self.mode and opecode in Const.Opecode.Continious.ALL:
            return
        self.bus.write_byte(Const.ADDRESS, opecode)
        self.mode = opecode
        self.first_valid = util.get_time_ms() + Const.MeasureTime.get_for_opecode(opecode)

    def set_mtreg(self, new: int) -> None:
        self.check_not_dry_mode()
        if not (Const.MTreg.MT_MIN <= new <= Const.MTreg.MT_MAX):
            raise ValueError(f"mtreg must be between {Const.MTreg.MT_MIN} and {Const.MTreg.MT_MAX} !!!")
        com_high = Const.MTreg.CHANGE_HIGH | (new >> 5)
        com_low = Const.MTreg.CHANGE_LOW | (new & 0b1_1111)
        self.bus.write_byte(Const.ADDRESS, com_high)
        self.bus.write_byte(Const.ADDRESS, com_low)
        self.mtreg = new
        self.first_valid = util.get_time_ms() + Const.MeasureTime.get_for_opecode(self.mode) * 2

    def get_result(self) -> float:
        self.check_not_dry_mode()
        if self.mode not in Const.Opecode.Continious.ALL and self.mode not in Const.Opecode.OneTime.ALL:
            raise ValueError("Not measuring in any mode!!!")
        self.wait_until_valid()
        raw = self.bus.read_word_data(Const.ADDRESS, self.mode)
        data = util.swap_bytes(raw)
        if Const.Opecode.is_H2_RES(self.mode):
            data >>= 1
        return data / 1.2 * (Const.MTreg.MT_DEFAULT / self.mtreg)

    def power_off(self) -> None:
        self.check_not_dry_mode()
        self.set_mode(Const.Opecode.POWER_OFF)

    def power_on(self) -> None:
        self.check_not_dry_mode()
        self.set_mode(Const.Opecode.POWER_ON)

    def reset(self) -> None:
        self.check_not_dry_mode()
        self.set_mode(Const.Opecode.RESET)
