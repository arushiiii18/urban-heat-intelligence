import sqlite3
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/urbanthermal.db")

def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS processed_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT, zone TEXT, lat REAL, lon REAL,
                temperature REAL, humidity REAL, wind_speed REAL,
                apparent_temperature REAL, building_density REAL,
                greenery_score REAL, water_distance REAL,
                rolling_3day_temp REAL, lag1_temp REAL,
                risk_score REAL, risk_tier TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS forecast_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT, zone TEXT, lat REAL, lon REAL,
                forecast_date TEXT, predicted_risk REAL, risk_tier TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acceleration_slopes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT, zone TEXT, lat REAL, lon REAL,
        slope REAL, r_squared REAL, p_value REAL,
        is_accelerating INTEGER,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_zone ON processed_zones(zone)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_city ON processed_zones(city)"))
        conn.commit()
    print(" Database initialized")

if __name__ == "__main__":
    init_db()