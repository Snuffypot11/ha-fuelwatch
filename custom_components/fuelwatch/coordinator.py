"""DataUpdateCoordinator for FuelWatch WA."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FuelStation, FuelWatchAPI
from .const import (
    CONF_BRAND,
    CONF_PRODUCT,
    CONF_REGION,
    CONF_SUBURB,
    CONF_SURROUNDING_SUBURBS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

WST = ZoneInfo("Australia/Perth")

# FuelWatch publishes tomorrow's prices at 2:30pm WST each day
TOMORROW_PUBLISH_HOUR = 14
TOMORROW_PUBLISH_MINUTE = 30


def _tomorrow_is_available() -> bool:
    """Return True if it's after 2:30pm WST (tomorrow's prices are published)."""
    now = datetime.now(WST)
    return now.hour > TOMORROW_PUBLISH_HOUR or (
        now.hour == TOMORROW_PUBLISH_HOUR and now.minute >= TOMORROW_PUBLISH_MINUTE
    )


class CoordinatorData:
    """Container for today + tomorrow station data."""

    def __init__(
        self,
        today: list[FuelStation],
        tomorrow: list[FuelStation],
        tomorrow_available: bool,
    ) -> None:
        self.today = today
        self.tomorrow = tomorrow
        self.tomorrow_available = tomorrow_available

    def find_today(self, key: str) -> FuelStation | None:
        return next((s for s in self.today if s.unique_key == key), None)

    def find_tomorrow(self, key: str) -> FuelStation | None:
        return next((s for s in self.tomorrow if s.unique_key == key), None)


class FuelWatchCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator that polls FuelWatch RSS for today and tomorrow prices."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_data: dict,
        scan_interval_seconds: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )
        session = async_get_clientsession(hass)
        self._api = FuelWatchAPI(session)
        self._region: int | None = config_data.get(CONF_REGION)
        self._product: int | None = config_data.get(CONF_PRODUCT)
        self._suburb: str | None = config_data.get(CONF_SUBURB) or None
        self._brand: str | None = config_data.get(CONF_BRAND) or None
        self._surrounding: bool = config_data.get(CONF_SURROUNDING_SUBURBS, False)

    def _api_kwargs(self) -> dict:
        return {
            "region": self._region,
            "product": self._product,
            "suburb": self._suburb,
            "brand": self._brand,
            "surrounding_suburbs": self._surrounding,
        }

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch today's prices, and tomorrow's if they're available."""
        try:
            today = await self._api.async_get_stations(**self._api_kwargs())
        except Exception as exc:
            raise UpdateFailed(f"Error fetching today's FuelWatch data: {exc}") from exc

        tomorrow: list[FuelStation] = []
        available = _tomorrow_is_available()

        if available:
            try:
                tomorrow = await self._api.async_get_stations(
                    **self._api_kwargs(), day="tomorrow"
                )
                _LOGGER.debug("Fetched %d tomorrow stations", len(tomorrow))
            except Exception as exc:
                # Tomorrow data is non-critical — log and continue with empty list
                _LOGGER.warning("Could not fetch tomorrow's FuelWatch prices: %s", exc)
                available = False

        return CoordinatorData(
            today=today,
            tomorrow=tomorrow,
            tomorrow_available=available,
        )
