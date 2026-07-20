"""INA219 UPS Hat sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
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
        VoltageSensor(coordinator),
        CurrentSensor(coordinator),
        PowerSensor(coordinator),
        SocSensor(coordinator),
        RemainingCapacitySensor(coordinator),
        RemainingTimeSensor(coordinator),
    ])


class INA219UpsHatSensor(INA219UpsHatEntity, SensorEntity):
    _attr_suggested_display_precision = 2
    _attr_state_class = SensorStateClass.MEASUREMENT


class VoltageSensor(INA219UpsHatSensor):
    _key = "voltage"
    _attr_name = "Voltage"
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE

    @property
    def native_value(self):
        return self.coordinator.data["voltage"]


class CurrentSensor(INA219UpsHatSensor):
    _key = "current"
    _attr_name = "Current"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT

    @property
    def native_value(self):
        return self.coordinator.data["current"]


class PowerSensor(INA219UpsHatSensor):
    _key = "power"
    _attr_name = "Power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER

    @property
    def native_value(self):
        return self.coordinator.data["power"]


class SocSensor(INA219UpsHatSensor):
    _key = "soc"
    _attr_name = "Battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_suggested_display_precision = 1

    @property
    def native_value(self):
        return self.coordinator.data["soc"]


class RemainingCapacitySensor(INA219UpsHatSensor):
    _key = "remaining_capacity"
    _attr_name = "Remaining Capacity"
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY_STORAGE
    _attr_suggested_display_precision = 0

    @property
    def native_value(self):
        return self.coordinator.data["remaining_battery_capacity"]


class RemainingTimeSensor(INA219UpsHatSensor):
    _key = "remaining_time"
    _attr_name = "Remaining Time"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_suggested_display_precision = 1

    @property
    def native_value(self):
        return self.coordinator.data["remaining_time"]
