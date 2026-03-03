import requests
import pandas as pd
import time
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.zones import ALL_ZONES

def fetch_historical(lat, lon, start="2021-01-01", end="2025-12-31"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,apparent_temperature",
        "timezone": "Asia/Kolkata"
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame({
        "timestamp":            data["hourly"]["time"],
        "temperature":          data["hourly"]["temperature_2m"],
        "humidity":             data["hourly"]["relativehumidity_2m"],
        "wind_speed":           data["hourly"]["windspeed_10m"],
        "apparent_temperature": data["hourly"]["apparent_temperature"],
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def build_training_data():
    all_dfs = []
    for z in ALL_ZONES:
        print(f"⏳ Fetching historical data: {z['city']} — {z['zone']}")
        try:
            df = fetch_historical(z["lat"], z["lon"])
            df["city"] = z["city"]
            df["zone"] = z["zone"]
            df["lat"]  = z["lat"]
            df["lon"]  = z["lon"]
            all_dfs.append(df)
            time.sleep(0.5)  # be respectful to the API
        except Exception as e:
            print(f"     Failed: {e}")
    
    full_df = pd.concat(all_dfs, ignore_index=True)
    os.makedirs("data", exist_ok=True)
    full_df.to_parquet("data/historical_raw.parquet", index=False)
    print(f"\n Done. Total rows: {len(full_df)}")
    print(f"   Saved to data/historical_raw.parquet")

if __name__ == "__main__":
    build_training_data()