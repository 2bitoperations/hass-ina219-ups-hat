"""INA219 UPS Hat coordinator."""

import logging

from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ADDR,
    CONF_BATTERIES_COUNT,
    CONF_BATTERY_CAPACITY,
    CONF_BUS,
    CONF_MAX_SOC,
    CONF_MIN_CHARGING_CURRENT,
    CONF_MIN_ONLINE_CURRENT,
    CONF_SCAN_INTERVAL,
    CONF_SMA_SAMPLES,
    DEFAULT_OCV,
    DOMAIN,
)
from .ina219.config import get_ina219_class
from .ina219_wrapper import INA219Wrapper
from .soc.provider import SocOcvProvider

_LOGGER = logging.getLogger(__name__)


class INA219UpsHatCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: core.HomeAssistant, entry: ConfigEntry, config: dict
    ) -> None:
        self.entry = entry
        self.name_prefix = config[CONF_NAME]

        self._addr = int(config[CONF_ADDR])
        self._bus = int(config[CONF_BUS])
        self._max_soc = config.get(CONF_MAX_SOC, 91)
        self._battery_capacity = config.get(CONF_BATTERY_CAPACITY)
        self._batteries_count = config.get(CONF_BATTERIES_COUNT, 3)
        self._sma_samples = config.get(CONF_SMA_SAMPLES, 5)
        self._min_online_current = config.get(CONF_MIN_ONLINE_CURRENT, -100)
        self._min_charging_current = config.get(CONF_MIN_CHARGING_CURRENT, 55)

        self._wrapper: INA219Wrapper | None = None
        self._soc_provider = SocOcvProvider(DEFAULT_OCV)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=config[CONF_SCAN_INTERVAL],
            update_method=self._update_data,
        )

    def _setup_hardware(self) -> None:
        """Initialize INA219 hardware (runs in executor thread)."""
        INA219 = get_ina219_class()
        ina219 = INA219(i2c_bus=self._bus, addr=self._addr)
        self._wrapper = INA219Wrapper(ina219, self._sma_samples)

    def _read_hardware(self) -> dict:
        """Read INA219 values and compute state (runs in executor thread)."""
        if self._wrapper is None:
            self._setup_hardware()

        w = self._wrapper
        w.measureINAValues()

        bus_voltage = w.getBusVoltageSMA_V()
        shunt_voltage = w.getShuntVoltageSMA_mV() / 1000
        total_voltage = bus_voltage + shunt_voltage
        current_ma = w.getCurrentSMA_mA()

        smooth_bus_voltage = w.getBusVoltageSMAx2_V()
        smooth_current_ma = w.getCurrentSMAx2_mA()

        cell_voltage = smooth_bus_voltage / self._batteries_count
        soc = min(self._soc_provider.get_soc_from_voltage(cell_voltage), self._max_soc)

        power = bus_voltage * (current_ma / 1000)

        current_ma_rounded = round(current_ma, 1)
        online = current_ma_rounded > self._min_online_current
        charging = current_ma_rounded > self._min_charging_current

        remaining_capacity_wh = None
        remaining_time_h = None
        if self._battery_capacity is not None:
            remaining_capacity_mah = (self._battery_capacity / 100.0) * soc
            remaining_capacity_wh = round(
                (remaining_capacity_mah * total_voltage) / 1000, 2
            )
            if not online and smooth_current_ma != 0:
                smooth_power = smooth_bus_voltage * (smooth_current_ma / 1000)
                if smooth_power < 0:
                    remaining_time_h = round(
                        remaining_capacity_wh / (-smooth_power), 1
                    )

        return {
            "voltage": round(total_voltage, 2),
            "current": round(current_ma / 1000, 2),
            "power": round(power, 2),
            "soc": round(soc, 1),
            "remaining_battery_capacity": remaining_capacity_wh,
            "remaining_time": remaining_time_h,
            "online": online,
            "charging": charging,
        }

    async def _update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._read_hardware)
        except Exception as e:
            raise UpdateFailed(f"Error reading INA219: {e}") from e

    def shutdown(self) -> None:
        """Close the SMBus file descriptor (call from executor thread)."""
        if self._wrapper is not None:
            self._wrapper._ina219.close()
            self._wrapper = None
