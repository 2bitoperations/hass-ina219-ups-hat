"""Wrapper for ina219 lib."""

from collections import deque

from .ina219.ina219_interface import INA219Interface

COEF_SMAx2 = 2


def _mean(values):
    lst = list(values)
    return sum(lst) / len(lst) if lst else 0.0


def _median(values):
    lst = sorted(values)
    n = len(lst)
    if n == 0:
        return 0.0
    mid = n // 2
    return lst[mid] if n % 2 else (lst[mid - 1] + lst[mid]) / 2.0


class INA219Wrapper:
    def __init__(self, ina219: INA219Interface, samples_cnt: int) -> None:
        self._ina219 = ina219
        self._bus_voltage_buf = deque(maxlen=samples_cnt * COEF_SMAx2)
        self._shunt_voltage_buf = deque(maxlen=samples_cnt)
        self._current_buf = deque(maxlen=samples_cnt * COEF_SMAx2)
        self._power_buf = deque(maxlen=samples_cnt)

    def measureINAValues(self):
        self._current_buf.append(self._ina219.getCurrent_mA())
        self._bus_voltage_buf.append(self._ina219.getBusVoltage_V())
        self._shunt_voltage_buf.append(self._ina219.getShuntVoltage_mV())
        self._power_buf.append(self._ina219.getPower_W())

    def getCurrentSMA_mA(self):
        return _mean(self._current_buf)

    def getBusVoltageSMA_V(self):
        return _mean(self._bus_voltage_buf)

    def getShuntVoltageSMA_mV(self):
        return _mean(self._shunt_voltage_buf)

    def getPowerSMA_W(self):
        return _mean(self._power_buf)

    def getCurrentSMAx2_mA(self):
        return _mean(self._getBufTail(self._current_buf, COEF_SMAx2))

    def getBusVoltageSMAx2_V(self):
        return _mean(self._getBufTail(self._bus_voltage_buf, COEF_SMAx2))

    def isBusVoltageBufFilled(self):
        return len(self._bus_voltage_buf) == self._bus_voltage_buf.maxlen

    def _getSMAValue(self, buf: deque, divider: int = 1):
        return _mean(self._getBufTail(buf, divider) if divider > 1 else buf)

    def _getSMMValue(self, buf: deque, divider: int = 1):
        return _median(self._getBufTail(buf, divider) if divider > 1 else buf)

    def _getBufTail(self, buf: deque, divider: int):
        lst = list(buf)
        slice_start = len(lst) - int(len(lst) / divider) - 1
        return lst[slice_start:]
