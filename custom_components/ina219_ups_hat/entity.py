"""INA219 UPS Hat entity base."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import INA219UpsHatCoordinator


class INA219UpsHatEntity(CoordinatorEntity[INA219UpsHatCoordinator]):
    """Base entity: one device per config entry, entities named relative to it."""

    _attr_has_entity_name = True
    _key: str  # subclasses must define this — used as unique_id suffix

    def __init__(self, coordinator: INA219UpsHatCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.name_prefix,
            manufacturer="Waveshare",
            model="INA219 UPS Hat",
        )

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.entry.entry_id}_{self._key}"
