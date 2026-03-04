import requests
import pandas as pd
import pickle
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.zones import ALL_ZONES
from utils.db import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent

FEATURES = [
    "temperature", "humidity", "wind_speed", "apparent_temperature",
    "building_density", "greenery_score", "water_distance",
    "rolling_3day_temp", "lag1_temp"
]

def fetch_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max,precipitation_sum",
        "hourly": "relativehumidity_2m,apparent_temperature",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7
    }
    r = requests.get(url, params=params)
    data = r.json()

    daily = data["daily"]
    hourly = data["hourly"]

    hourly_df = pd.DataFrame({
        "time": hourly["time"],
        "humidity": hourly["relativehumidity_2m"],
        "apparent_temperature": hourly["apparent_temperature"]
    })
    hourly_df["date"] = pd.to_datetime(hourly_df["time"]).dt.date
    daily_hourly = hourly_df.groupby("date").agg(
        humidity=("humidity", "mean"),
        apparent_temperature=("apparent_temperature", "mean")
    ).reset_index()

    forecast_df = pd.DataFrame({
        "forecast_date": pd.to_datetime(daily["time"]).date,
        "temperature": [(mx + mn) / 2 for mx, mn in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])],
        "wind_speed": daily["windspeed_10m_max"],
    })
    forecast_df = forecast_df.merge(daily_hourly, left_on="forecast_date", right_on="date", how="left")
    return forecast_df

def classify_risk(score):
    if score >= 60: return "High"
    elif score >= 35: return "Medium"
    else: return "Low"

def run():
    osm = pd.read_csv(BASE_DIR / "data" / "osm_features.csv")
    with open(BASE_DIR / "ml" / "artifacts" / "model.pkl", "rb") as f:
        model = pickle.load(f)
    engine = get_engine()

    all_records = []
    for z in ALL_ZONES:
        print(f" Forecast fetch: {z['city']} — {z['zone']}")
        try:
            forecast_df = fetch_forecast(z["lat"], z["lon"])
            osm_row = osm[(osm["city"] == z["city"]) & (osm["zone"] == z["zone"])].iloc[0]

            for _, row in forecast_df.iterrows():
                feature_row = {
                    "temperature":          row["temperature"],
                    "humidity":             row["humidity"],
                    "wind_speed":           row["wind_speed"],
                    "apparent_temperature": row["apparent_temperature"],
                    "building_density":     osm_row["building_density"],
                    "greenery_score":       osm_row["greenery_score"],
                    "water_distance":       osm_row["water_distance"],
                    "rolling_3day_temp":    row["temperature"],
                    "lag1_temp":            row["temperature"],
                }
                X = pd.DataFrame([feature_row])[FEATURES]
                predicted_risk = round(float(model.predict(X)[0]), 2)

                all_records.append({
                    "city":           z["city"],
                    "zone":           z["zone"],
                    "lat":            z["lat"],
                    "lon":            z["lon"],
                    "forecast_date":  str(row["forecast_date"]),
                    "predicted_risk": predicted_risk,
                    "risk_tier":      classify_risk(predicted_risk),
                    "created_at":     datetime.now(timezone.utc).isoformat()
                })
            print(f"    7 days forecast done")
        except Exception as e:
            print(f"    Failed: {e}")

    if not all_records:
        print("  No forecast records — check API or zone config")
        return

    # replace handles missing table + schema changes automatically
    df = pd.DataFrame(all_records)
    df.to_sql("forecast_scores", engine, if_exists="replace", index=False)
    print(f"\n Forecast scores written: {len(df)} rows")
    print(df[df["city"] == "Chennai"][["zone", "forecast_date", "predicted_risk", "risk_tier"]])

if __name__ == "__main__":
    run()