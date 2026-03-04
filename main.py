# LOCAL USE ONLY — Streamlit Cloud does not run this file.
# On cloud, the refresh button in the sidebar handles pipeline execution.
# Run locally with: python main.py
import subprocess
import sys
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time

def run_script(script_path):
    print(f"\n[{datetime.now().strftime('%d %b %Y, %I:%M %p')}] Running {script_path}...")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   Done: {script_path}")
    else:
        print(f"   Failed: {script_path}")
        print(result.stderr)

def run_pipeline():
    print(f"\n{'='*50}")
    print(f"Pipeline triggered at {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}")
    print(f"{'='*50}")
    run_script("ingestion/live_weather.py")
    run_script("ingestion/forecast_weather.py")
    run_script("ml/acceleration.py")
    print(f"\nPipeline complete. Dashboard data is fresh.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        hours=24,
        id="daily_pipeline",
        next_run_time=None  # don't run immediately on start, we run manually first
    )
    scheduler.start()
    print(f"Scheduler started. Pipeline will auto-refresh every 24 hours.")
    return scheduler

if __name__ == "__main__":
    print("UrbanThermal — Urban Heat Intelligence Platform")
    print("="*50)

    # run pipeline once on startup to get fresh data
    run_pipeline()

    # start background scheduler
    scheduler = start_scheduler()

    # launch streamlit dashboard
    print(f"\nLaunching dashboard...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard/app.py",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.shutdown()
        print("Scheduler stopped. Goodbye.")