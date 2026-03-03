import pandas as pd
import pickle
import sys
import os

# fix path resolution
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from sqlalchemy import create_engine

def get_db_engine():
    db_path = os.path.join(ROOT, "data", "urbanthermal.db")
    return create_engine(f"sqlite:///{db_path}")

def load_processed_zones():
    return pd.read_sql("SELECT * FROM processed_zones", get_db_engine())

def load_forecast():
    return pd.read_sql("SELECT * FROM forecast_scores", get_db_engine())

def load_acceleration():
    return pd.read_sql("SELECT * FROM acceleration_slopes", get_db_engine())

def load_model():
    with open(os.path.join(ROOT, "ml/artifacts/model.pkl"), "rb") as f:
        return pickle.load(f)

def load_features():
    with open(os.path.join(ROOT, "ml/artifacts/features.pkl"), "rb") as f:
        return pickle.load(f)

def load_feature_importance():
    with open(os.path.join(ROOT, "ml/artifacts/feature_importance.pkl"), "rb") as f:
        return pickle.load(f)

def classify_risk(score):
    if score >= 60: return "High"
    elif score >= 35: return "Medium"
    else: return "Low"

def risk_color(tier):
    return {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#2ecc71"}.get(tier, "#gray")

def get_last_updated():
    from datetime import datetime, timezone, timedelta
    result = pd.read_sql("SELECT MAX(fetched_at) as last_updated FROM processed_zones", get_db_engine())
    raw = result["last_updated"].iloc[0]
    utc_time = datetime.fromisoformat(str(raw).replace("+00:00", "")).replace(tzinfo=timezone.utc)
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return (
        utc_time.strftime("%d %b %Y, %I:%M %p"),
        ist_time.strftime("%d %b %Y, %I:%M %p")
    )