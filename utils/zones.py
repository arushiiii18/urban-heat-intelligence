ZONES = {
    "Delhi": [
        {"zone": "Connaught Place", "lat": 28.6315, "lon": 77.2167},
        {"zone": "Rohini",          "lat": 28.7041, "lon": 77.1025},
        {"zone": "Shahdara",        "lat": 28.6692, "lon": 77.2889},
        {"zone": "Dwarka",          "lat": 28.5921, "lon": 77.0460},
    ],
    "Mumbai": [
        {"zone": "Bandra",          "lat": 19.0596, "lon": 72.8295},
        {"zone": "Dharavi",         "lat": 19.0400, "lon": 72.8557},
        {"zone": "Borivali",        "lat": 19.2307, "lon": 72.8567},
        {"zone": "Colaba",          "lat": 18.9067, "lon": 72.8147},
    ],
    "Chennai": [
        {"zone": "Adyar",           "lat": 13.0012, "lon": 80.2565},
        {"zone": "Ambattur",        "lat": 13.1143, "lon": 80.1548},
        {"zone": "T Nagar",         "lat": 13.0418, "lon": 80.2341},
        {"zone": "Sholinganallur",  "lat": 12.9010, "lon": 80.2279},
    ],
    "Kolkata": [
        {"zone": "Salt Lake",       "lat": 22.5958, "lon": 88.4133},
        {"zone": "Howrah",          "lat": 22.5958, "lon": 88.2636},
        {"zone": "Park Street",     "lat": 22.5553, "lon": 88.3512},
        {"zone": "Dum Dum",         "lat": 22.6540, "lon": 88.3985},
    ],
    "Ahmedabad": [
        {"zone": "Navrangpura",     "lat": 23.0395, "lon": 72.5603},
        {"zone": "Maninagar",       "lat": 22.9973, "lon": 72.6024},
        {"zone": "Chandkheda",      "lat": 23.1068, "lon": 72.5878},
        {"zone": "Vatva",           "lat": 22.9597, "lon": 72.6490},
    ],
    "Jaipur": [
        {"zone": "Walled City",     "lat": 26.9239, "lon": 75.8267},
        {"zone": "Mansarovar",      "lat": 26.8529, "lon": 75.7694},
        {"zone": "Vaishali Nagar",  "lat": 26.9124, "lon": 75.7318},
        {"zone": "Malviya Nagar",   "lat": 26.8541, "lon": 75.8168},
    ],
}

ALL_ZONES = [
    {"city": city, **zone}
    for city, zones in ZONES.items()
    for zone in zones
]