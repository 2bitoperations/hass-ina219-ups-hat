"""INA219 UPS Hat binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import INA219UpsHatCoordinator
from .entity import INA219UpsHatEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: INA219UpsHatCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        OnlineBinarySensor(coordinator),
        ChargingBinarySensor(coordinator),
    ])


class INA219UpsHatBinarySensor(INA219UpsHatEntity, BinarySensorEntity):
    pass


class OnlineBinarySensor(INA219UpsHatBinarySensor):
    _key = "online"
    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    @property
    def is_on(self):
        return self.coordinator.data["online"]


class ChargingBinarySensor(INA219UpsHatBinarySensor):
    _key = "charging"
    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def is_on(self):
        return self.coordinator.data["charging"]
