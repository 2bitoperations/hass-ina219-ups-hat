"""Config flow for INA219 UPS Hat."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

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
    DEFAULT_NAME,
    DOMAIN,
)


def _parse_number(value) -> int:
    """Accept decimal integers or 0x-prefixed hex strings and return int."""
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip(), 0)
    except ValueError:
        raise vol.Invalid(
            "Enter a decimal number (e.g. 10) or hex with 0x prefix (e.g. 0x43)"
        )


STEP_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
    vol.Required(CONF_BUS, default="1"): vol.All(str, _parse_number),
    vol.Required(CONF_ADDR, default="0x40"): vol.All(str, _parse_number),
    vol.Required(CONF_BATTERIES_COUNT, default=3): int,
    vol.Required(CONF_BATTERY_CAPACITY, default=3000): int,
    vol.Optional(CONF_SCAN_INTERVAL, default=60): int,
    vol.Optional(CONF_MIN_ONLINE_CURRENT, default=-100): int,
    vol.Optional(CONF_MIN_CHARGING_CURRENT, default=55): int,
    vol.Optional(CONF_MAX_SOC, default=91): int,
    vol.Optional(CONF_SMA_SAMPLES, default=5): int,
})


def _validate_connection(bus: int, addr: int) -> str | None:
    """Return None on success or an error key on failure."""
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        b.read_byte(addr)
        b.close()
        return None
    except FileNotFoundError:
        return "bus_not_found"
    except OSError:
        return "device_not_found"
    except Exception:
        return "cannot_connect"


class INA219UpsHatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            error = await self.hass.async_add_executor_job(
                _validate_connection,
                user_input[CONF_BUS],
                user_input[CONF_ADDR],
            )
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_BUS]}_{user_input[CONF_ADDR]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return INA219UpsHatOptionsFlow(config_entry)


class INA219UpsHatOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        merged = {**self._entry.data, **self._entry.options}
        schema = vol.Schema({
            vol.Optional(CONF_BATTERIES_COUNT, default=merged.get(CONF_BATTERIES_COUNT, 3)): int,
            vol.Optional(CONF_BATTERY_CAPACITY, default=merged.get(CONF_BATTERY_CAPACITY, 3000)): int,
            vol.Optional(CONF_SCAN_INTERVAL, default=merged.get(CONF_SCAN_INTERVAL, 60)): int,
            vol.Optional(CONF_MIN_ONLINE_CURRENT, default=merged.get(CONF_MIN_ONLINE_CURRENT, -100)): int,
            vol.Optional(CONF_MIN_CHARGING_CURRENT, default=merged.get(CONF_MIN_CHARGING_CURRENT, 55)): int,
            vol.Optional(CONF_MAX_SOC, default=merged.get(CONF_MAX_SOC, 91)): int,
            vol.Optional(CONF_SMA_SAMPLES, default=merged.get(CONF_SMA_SAMPLES, 5)): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
