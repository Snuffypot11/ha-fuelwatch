"""Sensor platform for FuelWatch WA."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorStateClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FuelStation
from .const import CONF_PRODUCT, CONF_REGION, DOMAIN, PRODUCT_TYPES, REGIONS
from .coordinator import CoordinatorData, FuelWatchCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FuelWatch sensors from a config entry."""
    coordinator: FuelWatchCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()

    region = entry.data.get(CONF_REGION)
    product = entry.data.get(CONF_PRODUCT)

    entities: list[SensorEntity] = []

    # Summary sensors
    entities.append(FuelWatchCheapestTodaySensor(coordinator, entry, region, product))
    entities.append(FuelWatchAverageTodaySensor(coordinator, entry, region, product))
    entities.append(FuelWatchCheapestTomorrowSensor(coordinator, entry, region, product))

    # Per-station today + tomorrow sensor pairs
    seen_keys: set[str] = set()
    for station in coordinator.data.today or []:
        key = station.unique_key
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entities.append(FuelWatchStationTodaySensor(coordinator, entry, station))
        entities.append(FuelWatchStationTomorrowSensor(coordinator, entry, station))

    async_add_entities(entities, True)


def _device_info(entry: ConfigEntry, region: int, product: int) -> DeviceInfo:
    region_name = REGIONS.get(region, str(region))
    product_name = PRODUCT_TYPES.get(product, str(product))
    return DeviceInfo(
        identifiers={(DOMAIN, f"{region}_{product}")},
        name=f"FuelWatch {region_name} – {product_name}",
        manufacturer="FuelWatch WA",
        model=product_name,
        entry_type="service",
    )


# ---------------------------------------------------------------------------
# Summary sensors
# ---------------------------------------------------------------------------

class FuelWatchCheapestTodaySensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Cheapest price today across all stations."""

    _attr_icon = "mdi:gas-station"
    _attr_native_unit_of_measurement = "c/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, region, product):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{region}_{product}_cheapest_today"
        self._attr_name = "Cheapest Price Today"
        self._attr_device_info = _device_info(entry, region, product)

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.today:
            return None
        return min(s.price for s in data.today)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.today:
            return {}
        cheapest = min(data.today, key=lambda s: s.price)
        return {
            "station": cheapest.trading_name,
            "brand": cheapest.brand,
            "address": cheapest.address,
            "date": cheapest.date,
            "latitude": cheapest.latitude,
            "longitude": cheapest.longitude,
        }


class FuelWatchAverageTodaySensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Average price today across all stations."""

    _attr_icon = "mdi:gas-station-outline"
    _attr_native_unit_of_measurement = "c/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, region, product):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{region}_{product}_average_today"
        self._attr_name = "Average Price Today"
        self._attr_device_info = _device_info(entry, region, product)

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.today:
            return None
        prices = [s.price for s in data.today]
        return round(sum(prices) / len(prices), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: CoordinatorData = self.coordinator.data
        if not data:
            return {}
        return {"station_count": len(data.today)}


class FuelWatchCheapestTomorrowSensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Cheapest price tomorrow — only available after 2:30pm WST."""

    _attr_icon = "mdi:gas-station"
    _attr_native_unit_of_measurement = "c/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, region, product):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{region}_{product}_cheapest_tomorrow"
        self._attr_name = "Cheapest Price Tomorrow"
        self._attr_device_info = _device_info(entry, region, product)

    @property
    def available(self) -> bool:
        """Only mark available when tomorrow data has been published."""
        data: CoordinatorData = self.coordinator.data
        return (
            data is not None
            and data.tomorrow_available
            and len(data.tomorrow) > 0
            and super().available
        )

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.tomorrow_available or not data.tomorrow:
            return None
        return min(s.price for s in data.tomorrow)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.tomorrow_available or not data.tomorrow:
            return {}
        cheapest = min(data.tomorrow, key=lambda s: s.price)
        return {
            "station": cheapest.trading_name,
            "brand": cheapest.brand,
            "address": cheapest.address,
            "date": cheapest.date,
            "latitude": cheapest.latitude,
            "longitude": cheapest.longitude,
        }


# ---------------------------------------------------------------------------
# Per-station sensors
# ---------------------------------------------------------------------------

class FuelWatchStationTodaySensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Today's price for a single station."""

    _attr_icon = "mdi:gas-station"
    _attr_native_unit_of_measurement = "c/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, station: FuelStation):
        super().__init__(coordinator)
        self._station_key = station.unique_key
        region = entry.data.get(CONF_REGION, 0)
        product = entry.data.get(CONF_PRODUCT, 0)
        self._attr_unique_id = f"{DOMAIN}_{region}_{product}_{self._station_key}_today"
        self._attr_name = f"{station.trading_name}"
        self._attr_device_info = _device_info(entry, region, product)

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData = self.coordinator.data
        if not data:
            return None
        s = data.find_today(self._station_key)
        return s.price if s else None

    @property
    def available(self) -> bool:
        data: CoordinatorData = self.coordinator.data
        return data is not None and data.find_today(self._station_key) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: CoordinatorData = self.coordinator.data
        if not data:
            return {}
        s = data.find_today(self._station_key)
        if not s:
            return {}
        return {
            "brand": s.brand,
            "address": s.address,
            "location": s.location,
            "phone": s.phone,
            "trading_hours": s.trading_hours,
            "other_fuels": s.other_fuels,
            "date": s.date,
            "latitude": s.latitude,
            "longitude": s.longitude,
        }


class FuelWatchStationTomorrowSensor(CoordinatorEntity[FuelWatchCoordinator], SensorEntity):
    """Tomorrow's price for a single station.

    Returns None (unavailable) before 2:30pm WST and at/after midnight
    until the next day's prices are published.
    """

    _attr_icon = "mdi:gas-station-outline"
    _attr_native_unit_of_measurement = "c/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, station: FuelStation):
        super().__init__(coordinator)
        self._station_key = station.unique_key
        region = entry.data.get(CONF_REGION, 0)
        product = entry.data.get(CONF_PRODUCT, 0)
        self._attr_unique_id = f"{DOMAIN}_{region}_{product}_{self._station_key}_tomorrow"
        self._attr_name = f"{station.trading_name} Tomorrow"
        self._attr_device_info = _device_info(entry, region, product)

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.tomorrow_available:
            return None
        s = data.find_tomorrow(self._station_key)
        return s.price if s else None

    @property
    def available(self) -> bool:
        """Only mark available when tomorrow data exists for this station."""
        data: CoordinatorData = self.coordinator.data
        if not data or not data.tomorrow_available:
            return False
        return data.find_tomorrow(self._station_key) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data: CoordinatorData = self.coordinator.data
        if not data or not data.tomorrow_available:
            return {"published": False}
        s = data.find_tomorrow(self._station_key)
        if not s:
            return {"published": False}
        return {
            "published": True,
            "date": s.date,
            "brand": s.brand,
            "address": s.address,
            "trading_hours": s.trading_hours,
        }
