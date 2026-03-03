import osmnx as ox
import pandas as pd
import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.zones import ALL_ZONES

def get_building_density(lat, lon, dist=3000):
    try:
        gdf = ox.features_from_point((lat, lon), tags={"building": True}, dist=dist)
        return round(len(gdf) / 1000, 4)
    except:
        return None

def get_greenery_score(lat, lon, dist=3000):
    try:
        tags = {"landuse": ["forest", "grass", "meadow", "park"],
                "leisure": ["park", "garden"],
                "natural": ["wood", "scrub"]}
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=dist)
        return round(len(gdf) / 100, 4)
    except:
        return None

def get_water_distance(lat, lon, dist=5000):
    try:
        tags = {"natural": "water", "waterway": True}
        gdf = ox.features_from_point((lat, lon), tags=tags, dist=dist)
        if len(gdf) == 0:
            return 5.0  # max distance proxy if no water found
        return round(dist / (len(gdf) * 1000), 4)
    except:
        return 5.0

def build_osm_features():
    records = []
    for z in ALL_ZONES:
        print(f"⏳ OSM fetch: {z['city']} — {z['zone']}")
        records.append({
            "city":             z["city"],
            "zone":             z["zone"],
            "lat":              z["lat"],
            "lon":              z["lon"],
            "building_density": get_building_density(z["lat"], z["lon"]),
            "greenery_score":   get_greenery_score(z["lat"], z["lon"]),
            "water_distance":   get_water_distance(z["lat"], z["lon"]),
        })
        print(f"    buildings: {records[-1]['building_density']} | greenery: {records[-1]['greenery_score']} | water: {records[-1]['water_distance']}")
        time.sleep(1)

    df = pd.DataFrame(records)
    
    # fill any None values with city-level median
    for col in ["building_density", "greenery_score", "water_distance"]:
        df[col] = df.groupby("city")[col].transform(lambda x: x.fillna(x.median()))

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/osm_features.csv", index=False)
    print(f"\n OSM features saved for {len(df)} zones")
    print(df[["city", "zone", "building_density", "greenery_score", "water_distance"]])

if __name__ == "__main__":
    build_osm_features()