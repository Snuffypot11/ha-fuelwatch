# FuelWatch WA — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2022.8%2B-blue)](https://www.home-assistant.io/)

A Home Assistant integration for the [FuelWatch WA](https://www.fuelwatch.wa.gov.au) RSS feed.  
Monitor live fuel prices across Western Australia — by region, suburb, fuel type, and brand.

---

## Features

- 🔍 **Configurable** — choose region, fuel type, suburb, and brand filter via the UI
- 📊 **Per-station sensors** — one today + one tomorrow sensor per station
- 💰 **Summary sensors** — cheapest/average today, cheapest tomorrow
- ⏰ **Smart tomorrow handling** — tomorrow sensors go `unavailable` at midnight and repopulate at 2:35pm WST when FuelWatch publishes
- 🔄 **Timed triggers** — forced refresh at midnight and 2:35pm WST so prices always switch at the right time
- 📍 **Location attributes** — lat/lon on every sensor for map cards

---

## Installation via HACS

1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**
2. Add `https://github.com/Snuffypot11/ha-fuelwatch` as an **Integration**
3. Search for **FuelWatch WA** and install
4. Restart Home Assistant
5. **Settings → Devices & Services → Add Integration → FuelWatch WA**

---

## Configuration

| Field | Description | Default |
|---|---|---|
| **Region** | WA region code | 17 |
| **Fuel Type** | Product code | 2 |
| **Suburb** | Optional suburb — overrides region | *(none)* |
| **Brand** | Filter to one brand | Any |
| **Surrounding suburbs** | Include nearby suburbs | false |
| **Scan interval** | Seconds between polls (min 300) | 3600 |

### Region Codes

| Code | Region | Code | Region |
|---|---|---|---|
| 25 | Metro: North of River | 39 | Dongara |
| 26 | Metro: South of River | 31 | Donnybrook / Balingup |
| 27 | Metro: East/Hills | 7 | Esperance |
| 15 | Albany | 40 | Exmouth |
| 28 | Augusta / Margaret River | 41 | Fitzroy Crossing |
| 63 | Bodallin | 17 | Geraldton |
| 1 | Boulder | 21 | Greenough |
| 30 | Bridgetown / Greenbushes | 22 | Harvey |
| 2 | Broome | 42 | Jurien |
| 16 | Bunbury | 8 | Kalgoorlie |
| 3 | Busselton (Townsite) | 43 | Kambalda |
| 29 | Busselton (Shire) | 9 | Karratha |
| 19 | Capel | 44 | Kellerberrin |
| 4 | Carnarvon | 45 | Kojonup |
| 33 | Cataby | 10 | Kununurra |
| 5 | Collie | 18 | Mandurah |
| 34 | Coolgardie | 32 | Manjimup |
| 35 | Cunderdin | 58 | Meckering |
| 36 | Dalwallinu | 46 | Meekatharra |
| 6 | Dampier | 47 | Moora |
| 20 | Dardanup | 48 | Mount Barker |
| 37 | Denmark | 61 | Munglinup |
| 38 | Derby | 23 | Murray |
| 11 | Narrogin | 50 | Norseman |
| 49 | Newman | 60 | North Bannister |
| 12 | Northam | 13 | Port Hedland |
| 62 | Northam (Shire) | 51 | Ravensthorpe |
| 57 | Regans Ford | 53 | Tammin |
| 14 | South Hedland | 24 | Waroona |
| 54 | Williams | 55 | Wubin |
| 59 | Wundowie | 56 | York |

### Fuel Type Codes

| Code | Fuel |
|---|---|
| 1 | Unleaded Petrol |
| 2 | Premium Unleaded |
| 4 | Diesel |
| 5 | LPG |
| 6 | 98 RON |
| 10 | E85 |
| 11 | Brand Diesel |

---

## Sensors Created

For each configured entry the integration creates:

| Sensor | Description |
|---|---|
| `…_cheapest_price_today` | Lowest price across all stations today |
| `…_average_price_today` | Mean price across all stations today |
| `…_cheapest_price_tomorrow` | Lowest price tomorrow (unavailable before 2:35pm WST) |
| `…_<station>` | Today's price for a specific station |
| `…_<station>_tomorrow` | Tomorrow's price for a station (unavailable before 2:35pm WST) |

All sensors have `state_class: measurement` — HA records their history automatically.

### Tomorrow sensor lifecycle

| Time (WST) | Tomorrow sensors |
|---|---|
| Midnight → 2:34pm | `unavailable` — no stale data shown |
| 2:35pm → 11:59pm | Live tomorrow prices |
| Midnight | Immediately cleared by timed trigger |

> **Timezone note:** The timed refresh triggers use your HA instance timezone. Make sure HA is set to `Australia/Perth` in **Settings → System → General** for the midnight and 2:35pm triggers to fire at the correct local time.

---

## License

MIT
