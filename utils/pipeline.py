import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

def refresh():
    from utils.db import init_db
    from ingestion.live_weather import run as live_run
    from ingestion.forecast_weather import run as forecast_run
    from ml.acceleration import compute_slopes

    init_db()       #CREATE TABLE IF NOT EXISTS
    live_run()
    forecast_run()
    compute_slopes()

if __name__ == "__main__":
    refresh()