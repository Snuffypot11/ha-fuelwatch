"""Constants for FuelWatch WA integration."""

DOMAIN = "fuelwatch"
PLATFORMS = ["sensor"]

# RSS feed base URL
FUELWATCH_RSS_URL = "https://www.fuelwatch.wa.gov.au/fuelwatch/fuelWatchRSS"

# Default scan interval in seconds (prices update once daily ~2:30pm)
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour

# Config entry keys
CONF_REGION = "region"
CONF_PRODUCT = "product"
CONF_SUBURB = "suburb"
CONF_BRAND = "brand"
CONF_SURROUNDING_SUBURBS = "surrounding_suburbs"

# FuelWatch product codes
PRODUCT_TYPES = {
    1: "Unleaded Petrol",
    2: "Premium Unleaded",
    4: "Diesel",
    5: "LPG",
    6: "98 RON",
    10: "E85",
    11: "Brand Diesel",
}

# FuelWatch region codes
REGIONS = {
    25: "Metro: North of River",
    26: "Metro: South of River",
    27: "Metro: East/Hills",
    15: "Albany",
    28: "Augusta / Margaret River",
    63: "Bodallin",
    1:  "Boulder",
    30: "Bridgetown / Greenbushes",
    2:  "Broome",
    16: "Bunbury",
    3:  "Busselton (Townsite)",
    29: "Busselton (Shire)",
    19: "Capel",
    4:  "Carnarvon",
    33: "Cataby",
    5:  "Collie",
    34: "Coolgardie",
    35: "Cunderdin",
    36: "Dalwallinu",
    6:  "Dampier",
    20: "Dardanup",
    37: "Denmark",
    38: "Derby",
    39: "Dongara",
    31: "Donnybrook / Balingup",
    7:  "Esperance",
    40: "Exmouth",
    41: "Fitzroy Crossing",
    17: "Geraldton",
    21: "Greenough",
    22: "Harvey",
    42: "Jurien",
    8:  "Kalgoorlie",
    43: "Kambalda",
    9:  "Karratha",
    44: "Kellerberrin",
    45: "Kojonup",
    10: "Kununurra",
    18: "Mandurah",
    32: "Manjimup",
    58: "Meckering",
    46: "Meekatharra",
    47: "Moora",
    48: "Mount Barker",
    61: "Munglinup",
    23: "Murray",
    11: "Narrogin",
    49: "Newman",
    50: "Norseman",
    60: "North Bannister",
    12: "Northam",
    62: "Northam (Shire)",
    13: "Port Hedland",
    51: "Ravensthorpe",
    57: "Regans Ford",
    14: "South Hedland",
    53: "Tammin",
    24: "Waroona",
    54: "Williams",
    55: "Wubin",
    59: "Wundowie",
    56: "York",
}

# Brand display names (for filtering)
KNOWN_BRANDS = [
    "Any",
    "7-Eleven",
    "Ampol",
    "BP",
    "Caltex",
    "Coles Express",
    "Costco",
    "EG Group",
    "Gull",
    "Liberty",
    "Metro Petroleum",
    "Puma Energy",
    "Shell",
    "United",
    "Vibe",
    "Woolworths",
    "Z Energy",
]

# RSS item field names
RSS_FIELD_PRICE = "price"
RSS_FIELD_TRADING_NAME = "trading-name"
RSS_FIELD_BRAND = "brand"
RSS_FIELD_ADDRESS = "address"
RSS_FIELD_LOCATION = "location"
RSS_FIELD_PHONE = "phone"
RSS_FIELD_LATITUDE = "latitude"
RSS_FIELD_LONGITUDE = "longitude"
RSS_FIELD_DATE = "date"
RSS_FIELD_TRADING_HOURS = "trading-hours"
RSS_FIELD_OTHER_FUELS = "other-fuels"
