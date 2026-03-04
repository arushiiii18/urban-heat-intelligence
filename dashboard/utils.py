import pandas as pd
import pickle
import sys
import os
from sqlalchemy import create_engine, inspect, text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(ROOT, "data", "urbanthermal.db")

def get_db_engine():
    return create_engine(f"sqlite:///{DB_PATH}")

def table_exists(table_name: str) -> bool:
    """Returns True only if the table exists AND has at least one row."""
    try:
        engine = get_db_engine()
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        #check it's not empty
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            return result > 0
    except Exception:
        return False

def load_processed_zones():
    return pd.read_sql("SELECT * FROM processed_zones", get_db_engine())

def load_forecast():
    return pd.read_sql("SELECT * FROM forecast_scores", get_db_engine())

def load_acceleration():
    return pd.read_sql("SELECT * FROM acceleration_slopes", get_db_engine())

def load_model():
    with open(os.path.join(ROOT, "ml", "artifacts", "model.pkl"), "rb") as f:
        return pickle.load(f)

def load_features():
    with open(os.path.join(ROOT, "ml", "artifacts", "features.pkl"), "rb") as f:
        return pickle.load(f)

def load_feature_importance():
    with open(os.path.join(ROOT, "ml", "artifacts", "feature_importance.pkl"), "rb") as f:
        return pickle.load(f)

def classify_risk(score):
    if score >= 60:   return "High"
    elif score >= 35: return "Medium"
    else:             return "Low"

def risk_color(tier):
    return {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#2ecc71"}.get(tier, "#aaaaaa")

#Bug fix: was crashing when MAX(fetched_at) returns NULL
def get_last_updated():
    from datetime import datetime, timezone, timedelta

    try:
        engine = get_db_engine()
        inspector = inspect(engine)
        if "processed_zones" not in inspector.get_table_names():
            return "No data yet", "No data yet"

        result = pd.read_sql(
            "SELECT MAX(fetched_at) as last_updated FROM processed_zones",
            engine
        )
        raw = result["last_updated"].iloc[0]

        # NULL guard — table exists but is empty
        if raw is None or str(raw) in ("None", "NaT", ""):
            return "No data yet", "No data yet"

        utc_time = datetime.fromisoformat(str(raw).replace("+00:00", "")).replace(tzinfo=timezone.utc)
        ist_time = utc_time + timedelta(hours=5, minutes=30)
        return (
            utc_time.strftime("%d %b %Y, %I:%M %p"),
            ist_time.strftime("%d %b %Y, %I:%M %p"),
        )
    except Exception as e:
        return f"Error: {e}", "—"