import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_data():
    weather = pd.read_parquet("data/historical_raw.parquet")
    osm = pd.read_csv("data/osm_features.csv")
    return weather, osm

def compute_risk_score(row):
    temp_score     = min((row["temperature"] / 45) * 40, 40)
    humidity_score = min((row["humidity"] / 100) * 20, 20)
    building_score = min((row["building_density"] / 60) * 20, 20)
    greenery_score = max(0, 10 - (row["greenery_score"] * 2))
    wind_score     = max(0, 10 - (row["wind_speed"] * 2))
    return round(temp_score + humidity_score + building_score + greenery_score + wind_score, 2)

def classify_risk(score):
    if score >= 60: return "High"
    elif score >= 35: return "Medium"
    else: return "Low"

def engineer_features(weather, osm):
    print("⏳ Computing daily aggregates...")
    weather["date"] = weather["timestamp"].dt.date
    
    daily = weather.groupby(["city", "zone", "lat", "lon", "date"]).agg(
        temperature          = ("temperature", "mean"),
        humidity             = ("humidity", "mean"),
        wind_speed           = ("wind_speed", "mean"),
        apparent_temperature = ("apparent_temperature", "mean"),
    ).reset_index()

    daily = daily.sort_values(["city", "zone", "date"])

    print("⏳ Computing rolling and lag features...")
    daily["rolling_3day_temp"] = (
        daily.groupby(["city", "zone"])["temperature"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )
    daily["lag1_temp"] = (
        daily.groupby(["city", "zone"])["temperature"]
        .transform(lambda x: x.shift(1))
    )
    daily["lag1_temp"] = daily["lag1_temp"].fillna(daily["temperature"])

    print(" Merging OSM features...")
    df = daily.merge(osm[["city", "zone", "building_density", "greenery_score", "water_distance"]], 
                     on=["city", "zone"], how="left")

    print(" Computing risk scores...")
    df["risk_score"] = df.apply(compute_risk_score, axis=1)
    df["risk_tier"]  = df["risk_score"].apply(classify_risk)

    return df

def run():
    weather, osm = load_data()
    print(f" Weather rows: {len(weather)} | OSM zones: {len(osm)}")
    
    df = engineer_features(weather, osm)
    
    os.makedirs("data", exist_ok=True)
    df.to_parquet("data/training_data.parquet", index=False)
    
    print(f"\n Feature engineering done")
    print(f"   Total rows: {len(df)}")
    print(f"   Date range: {df['date'].min()} → {df['date'].max()}")
    print(f"   Zones: {df['zone'].nunique()} | Cities: {df['city'].nunique()}")
    print(f"\nRisk tier distribution:")
    print(df["risk_tier"].value_counts())
    print(f"\nSample:")
    print(df[["city", "zone", "date", "temperature", "humidity", "building_density", "greenery_score", "risk_score", "risk_tier"]].head(10))

if __name__ == "__main__":
    run()