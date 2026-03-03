import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def refresh():
    from ingestion.live_weather import run as live_run
    from ingestion.forecast_weather import run as forecast_run
    from ml.acceleration import compute_slopes
    live_run()
    forecast_run()
    compute_slopes()