"""FuelWatch WA Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, PLATFORMS
from .coordinator import FuelWatchCoordinator

_LOGGER = logging.getLogger(__name__)

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FuelWatch from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = FuelWatchCoordinator(hass, dict(entry.data), scan_interval)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # -----------------------------------------------------------------------
    # Timed refresh triggers (WST = UTC+8, so we use UTC times here)
    # HA's async_track_time_change uses the HA instance timezone.
    # We trigger at:
    #   - 00:00:05 — clears tomorrow sensors right after midnight
    #   - 14:35:00 — picks up tomorrow prices ~5 min after FuelWatch publishes
    # If your HA timezone is set to Perth these times are correct as-is.
    # If HA is set to UTC, change hour=0 -> hour=16 and hour=14 -> hour=6.
    # -----------------------------------------------------------------------

    async def _refresh(_now=None) -> None:
        _LOGGER.debug("FuelWatch scheduled refresh triggered")
        await coordinator.async_refresh()

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _refresh,
            hour=0,
            minute=0,
            second=5,
        )
    )

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _refresh,
            hour=14,
            minute=35,
            second=0,
        )
    )

    # Re-load when options are changed
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
