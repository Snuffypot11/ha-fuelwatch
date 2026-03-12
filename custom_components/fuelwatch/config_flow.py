"""Config flow for FuelWatch WA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BRAND,
    CONF_PRODUCT,
    CONF_REGION,
    CONF_SUBURB,
    CONF_SURROUNDING_SUBURBS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KNOWN_BRANDS,
    PRODUCT_TYPES,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)

CONF_SCAN_INTERVAL = "scan_interval"


def _build_region_selector() -> dict:
    return {str(k): f"{k} – {v}" for k, v in sorted(REGIONS.items())}


def _build_product_selector() -> dict:
    return {str(k): f"{k} – {v}" for k, v in sorted(PRODUCT_TYPES.items())}


async def _validate_feed(hass: HomeAssistant, region: int, product: int) -> bool:
    """Try fetching the RSS feed to verify the config is valid."""
    from .api import FuelWatchAPI

    session = async_get_clientsession(hass)
    api = FuelWatchAPI(session)
    try:
        stations = await api.async_get_stations(region=region, product=product)
        return len(stations) >= 0  # even empty list is valid
    except Exception:
        return False


class FuelWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for FuelWatch WA."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            region = int(user_input[CONF_REGION])
            product = int(user_input[CONF_PRODUCT])

            # Prevent duplicate entries for same region+product
            await self.async_set_unique_id(f"{region}_{product}")
            self._abort_if_unique_id_configured()

            valid = await _validate_feed(self.hass, region, product)
            if not valid:
                errors["base"] = "cannot_connect"
            else:
                region_name = REGIONS.get(region, str(region))
                product_name = PRODUCT_TYPES.get(product, str(product))
                return self.async_create_entry(
                    title=f"FuelWatch – {region_name} / {product_name}",
                    data={
                        CONF_REGION: region,
                        CONF_PRODUCT: product,
                        CONF_SUBURB: user_input.get(CONF_SUBURB, ""),
                        CONF_BRAND: user_input.get(CONF_BRAND, "Any"),
                        CONF_SURROUNDING_SUBURBS: user_input.get(
                            CONF_SURROUNDING_SUBURBS, False
                        ),
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    },
                )

        region_options = _build_region_selector()
        product_options = _build_product_selector()

        schema = vol.Schema(
            {
                vol.Required(CONF_REGION): vol.In(region_options),
                vol.Required(CONF_PRODUCT): vol.In(product_options),
                vol.Optional(CONF_SUBURB, default=""): str,
                vol.Optional(CONF_BRAND, default="Any"): vol.In(KNOWN_BRANDS),
                vol.Optional(CONF_SURROUNDING_SUBURBS, default=False): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=300, max=86400)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "rss_url": "https://www.fuelwatch.wa.gov.au/tools/rss"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FuelWatchOptionsFlow:
        """Return options flow so users can edit settings after setup."""
        return FuelWatchOptionsFlow(config_entry)


class FuelWatchOptionsFlow(config_entries.OptionsFlow):
    """Handle options (re-configure after initial setup)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SUBURB, default=current.get(CONF_SUBURB, "")
                ): str,
                vol.Optional(
                    CONF_BRAND, default=current.get(CONF_BRAND, "Any")
                ): vol.In(KNOWN_BRANDS),
                vol.Optional(
                    CONF_SURROUNDING_SUBURBS,
                    default=current.get(CONF_SURROUNDING_SUBURBS, False),
                ): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=300, max=86400)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
