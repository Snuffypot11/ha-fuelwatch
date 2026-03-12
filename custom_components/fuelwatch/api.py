"""FuelWatch RSS API client."""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

from aiohttp import ClientSession, ClientError

from .const import FUELWATCH_RSS_URL

_LOGGER = logging.getLogger(__name__)


@dataclass
class FuelStation:
    """Represents a single fuel station from FuelWatch RSS."""

    trading_name: str
    brand: str
    price: float
    address: str
    location: str
    phone: str
    latitude: Optional[float]
    longitude: Optional[float]
    date: str
    trading_hours: str
    other_fuels: str

    @property
    def unique_key(self) -> str:
        """Slug used as sensor unique_id suffix."""
        slug = (
            self.trading_name.lower()
            .replace(" ", "_")
            .replace("'", "")
            .replace("/", "_")
            .replace("&", "and")
            .replace(",", "")
            .replace(".", "")
        )
        addr_slug = self.address.split(" ")[0].lower() if self.address else ""
        return f"{slug}_{addr_slug}" if addr_slug else slug


class FuelWatchAPI:
    """Async client for FuelWatch RSS."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    def _build_url(
        self,
        region: int | None = None,
        product: int | None = None,
        suburb: str | None = None,
        brand: str | None = None,
        surrounding_suburbs: bool = False,
        day: str | None = None,
    ) -> str:
        """Build the RSS URL.

        Args:
            day: None for today, "tomorrow" for tomorrow's prices,
                 or "YYYY-MM-DD" for a specific past date (up to 7 days back).
        """
        params: list[str] = []
        if product:
            params.append(f"Product={product}")
        if region:
            params.append(f"Region={region}")
        if suburb:
            params.append(f"Suburb={suburb}")
        if brand and brand != "Any":
            params.append(f"Brand={brand}")
        if surrounding_suburbs:
            params.append("Surrounding=yes")
        if day:
            params.append(f"Day={day}")
        query = "&".join(params)
        return f"{FUELWATCH_RSS_URL}?{query}" if query else FUELWATCH_RSS_URL

    async def async_get_stations(
        self,
        region: int | None = None,
        product: int | None = None,
        suburb: str | None = None,
        brand: str | None = None,
        surrounding_suburbs: bool = False,
        day: str | None = None,
    ) -> list[FuelStation]:
        """Fetch and parse FuelWatch RSS, returning a list of FuelStation objects."""
        url = self._build_url(region, product, suburb, brand, surrounding_suburbs, day)
        _LOGGER.debug("Fetching FuelWatch RSS: %s", url)

        try:
            async with self._session.get(url, timeout=15) as response:
                response.raise_for_status()
                xml_text = await response.text()
        except ClientError as exc:
            _LOGGER.error("Error fetching FuelWatch RSS from %s: %s", url, exc)
            raise

        return self._parse_xml(xml_text)

    def _parse_xml(self, xml_text: str) -> list[FuelStation]:
        stations: list[FuelStation] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            _LOGGER.error("Failed to parse FuelWatch XML: %s", exc)
            return stations

        channel = root.find("channel")
        if channel is None:
            _LOGGER.warning("No <channel> found in FuelWatch RSS")
            return stations

        for item in channel.findall("item"):
            price_text = item.findtext("price", "").strip()
            trading_name = item.findtext("trading-name", "").strip()

            if not price_text or not trading_name:
                continue

            try:
                price = float(price_text)
            except ValueError:
                _LOGGER.debug("Skipping station with invalid price: %s", price_text)
                continue

            lat_text = item.findtext("latitude", "")
            lon_text = item.findtext("longitude", "")
            try:
                lat = float(lat_text) if lat_text else None
                lon = float(lon_text) if lon_text else None
            except ValueError:
                lat = lon = None

            stations.append(
                FuelStation(
                    trading_name=trading_name,
                    brand=item.findtext("brand", "").strip(),
                    price=price,
                    address=item.findtext("address", "").strip(),
                    location=item.findtext("location", "").strip(),
                    phone=item.findtext("phone", "").strip(),
                    latitude=lat,
                    longitude=lon,
                    date=item.findtext("date", "").strip(),
                    trading_hours=item.findtext("trading-hours", "").strip(),
                    other_fuels=item.findtext("other-fuels", "").strip(),
                )
            )

        _LOGGER.debug("Parsed %d stations from FuelWatch RSS", len(stations))
        return stations
