import requests
import pandas as pd
import pickle
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.zones import ALL_ZONES
from utils.db import get_engine
from sqlalchemy import text

FEATURES = [
    "temperature", "humidity", "wind_speed", "apparent_temperature",
    "building_density", "greenery_score", "water_distance",
    "rolling_3day_temp", "lag1_temp"
]

def fetch_current_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relativehumidity_2m,windspeed_10m,apparent_temperature",
        "timezone": "Asia/Kolkata"
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    d = r.json()["current"]
    return {
        "temperature":          d["temperature_2m"],
        "humidity":             d["relativehumidity_2m"],
        "wind_speed":           d["windspeed_10m"],
        "apparent_temperature": d["apparent_temperature"],
    }

def load_artifacts():
    with open(ROOT / "ml" / "artifacts" / "model.pkl", "rb") as f:
        return pickle.load(f)

def classify_risk(score):
    if score >= 60:   return "High"
    elif score >= 35: return "Medium"
    else:             return "Low"

def run():
    osm    = pd.read_csv(ROOT / "data" / "osm_features.csv")
    model  = load_artifacts()
    engine = get_engine()

    records = []
    for z in ALL_ZONES:
        print(f"Live fetch: {z['city']} — {z['zone']}")
        try:
            weather = fetch_current_weather(z["lat"], z["lon"])
            osm_row = osm[
                (osm["city"] == z["city"]) & (osm["zone"] == z["zone"])
            ].iloc[0]

            row = {
                "city":                 z["city"],
                "zone":                 z["zone"],
                "lat":                  z["lat"],
                "lon":                  z["lon"],
                "temperature":          weather["temperature"],
                "humidity":             weather["humidity"],
                "wind_speed":           weather["wind_speed"],
                "apparent_temperature": weather["apparent_temperature"],
                "building_density":     osm_row["building_density"],
                "greenery_score":       osm_row["greenery_score"],
                "water_distance":       osm_row["water_distance"],
                "rolling_3day_temp":    weather["temperature"],
                "lag1_temp":            weather["temperature"],
                "fetched_at":           datetime.now(timezone.utc).isoformat(),
            }

            X = pd.DataFrame([row])[FEATURES]
            row["risk_score"] = round(float(model.predict(X)[0]), 2)
            row["risk_tier"]  = classify_risk(row["risk_score"])
            records.append(row)
            print(f"    ✓ risk_score={row['risk_score']} | tier={row['risk_tier']}")

        except Exception as e:
            print(f"    ✗ Failed for {z['zone']}: {e}")

    if not records:
        print(" No records fetched — check API or zone config")
        return

    df = pd.DataFrame(records)

    #clear today's snapshot rows then append fresh ones.
    # This keeps historical rows intact if you ever want them.
    with engine.connect() as conn:
        conn.execute(text(
            "DELETE FROM processed_zones WHERE fetched_at >= date('now', 'start of day')"
        ))
        conn.commit()

    df.to_sql("processed_zones", engine, if_exists="append", index=False)
    print(f"\n Live scores written for {len(df)} zones")
    print(df[["city", "zone", "temperature", "risk_score", "risk_tier"]].to_string(index=False))

if __name__ == "__main__":
    run()