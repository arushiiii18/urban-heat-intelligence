import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db import get_engine
from utils.zones import ALL_ZONES

#absolute path so it works on ANY machine
BASE_DIR = Path(__file__).resolve().parent.parent
PARQUET_PATH = BASE_DIR / "data" / "training_data.parquet"


def _load_training_data(engine) -> pd.DataFrame:
    """
    Load temperature data with a clear priority order:
      1. Live DB  ← always preferred for 'refresh live data'
      2. Parquet  ← fallback for cold-start / offline
    """
    try:
        df = pd.read_sql("SELECT city, zone, date, temperature FROM weather_data", engine)
        if df.empty:
            raise ValueError("DB returned empty — falling back to parquet")
        print("  Loaded data from DB")
        return df
    except Exception as e:
        print(f"  DB load failed ({e}), falling back to parquet...")
        if not PARQUET_PATH.exists():
            raise FileNotFoundError(
                f"No DB data AND no parquet found at {PARQUET_PATH}. "
                "Run the data ingestion pipeline first."
            )
        return pd.read_parquet(PARQUET_PATH)


def compute_slopes() -> pd.DataFrame:
    engine = get_engine()

    #load data
    df = _load_training_data(engine)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    #yearly averages per zone
    yearly = (
        df.groupby(["city", "zone", "year"])["temperature"]
        .mean()
        .reset_index()
        .rename(columns={"temperature": "avg_temp"})
    )

    #linear regression per zone 
    records = []
    skipped = []

    for z in ALL_ZONES:
        zone_data = yearly[
            (yearly["city"] == z["city"]) & (yearly["zone"] == z["zone"])
        ]

        if len(zone_data) < 3:
            skipped.append(f"{z['city']}/{z['zone']}")
            continue

        slope, _, r_value, p_value, std_err = stats.linregress(
            zone_data["year"], zone_data["avg_temp"]
        )

        records.append({
            "city":       z["city"],
            "zone":       z["zone"],
            "lat":        z["lat"],
            "lon":        z["lon"],
            "slope":      round(slope, 4),
            "r_squared":  round(r_value ** 2, 4),
            "p_value":    round(p_value, 4),
            "std_err":    round(std_err, 4),        # extra: useful for uncertainty display
            "n_years":    len(zone_data),           # extra: transparency on data quality
        })

    if skipped:
        print(f"  Skipped (< 3 years of data): {', '.join(skipped)}")

    if not records:
        raise ValueError("No zones had enough data to compute slopes. Check your data pipeline.")

    df_slopes = pd.DataFrame(records)

    #acceleration flag: top 20% slope AND statistically significant
    threshold = df_slopes["slope"].quantile(0.80)
    df_slopes["is_accelerating"] = (
        (df_slopes["slope"] >= threshold) & (df_slopes["p_value"] < 0.05)
    ).astype(int)

    #log 
    print("\n  Heat Acceleration Rankings:")
    print(
        df_slopes[["city", "zone", "slope", "r_squared", "p_value", "is_accelerating"]]
        .sort_values("slope", ascending=False)
        .to_string(index=False)
    )
    print(f"\n  Acceleration threshold (top 20%): {round(threshold, 4)}°C/year")
    print(f"  Accelerating zones (slope ≥ threshold & p < 0.05): {df_slopes['is_accelerating'].sum()}")

    #persist
    df_slopes.to_sql("acceleration_slopes", engine, if_exists="replace", index=False)
    print("  Acceleration slopes saved to DB\n")

    return df_slopes


if __name__ == "__main__":
    compute_slopes()