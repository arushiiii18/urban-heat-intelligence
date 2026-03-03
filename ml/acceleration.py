import pandas as pd
import numpy as np
from scipy import stats
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db import get_engine
from utils.zones import ALL_ZONES
from sqlalchemy import text

def compute_slopes():
    df = pd.read_parquet("data/training_data.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    yearly = df.groupby(["city", "zone", "year"])["temperature"].mean().reset_index()
    yearly.columns = ["city", "zone", "year", "avg_temp"]

    records = []
    for z in ALL_ZONES:
        zone_data = yearly[(yearly["city"] == z["city"]) & (yearly["zone"] == z["zone"])]
        
        if len(zone_data) < 3:
            continue

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            zone_data["year"], zone_data["avg_temp"]
        )

        records.append({
            "city":  z["city"],
            "zone":  z["zone"],
            "lat":   z["lat"],
            "lon":   z["lon"],
            "slope": round(slope, 4),
            "r_squared": round(r_value**2, 4),
            "p_value": round(p_value, 4),
        })

    df_slopes = pd.DataFrame(records)

    # top 20% slopes = accelerating zones
    threshold = df_slopes["slope"].quantile(0.80)
    df_slopes["is_accelerating"] = (df_slopes["slope"] >= threshold).astype(int)

    print("🌡️  Heat Acceleration Rankings:")
    print(df_slopes.sort_values("slope", ascending=False).to_string(index=False))
    print(f"\n   Acceleration threshold (top 20%): {round(threshold, 4)}°C/year")
    print(f"   Accelerating zones: {df_slopes['is_accelerating'].sum()}")

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM acceleration_slopes"))
        conn.commit()

    df_slopes.to_sql("acceleration_slopes", engine, if_exists="append", index=False)
    print(" Acceleration slopes saved")
    return df_slopes

if __name__ == "__main__":
    compute_slopes()