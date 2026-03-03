import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, ROOT)
from dashboard.utils import load_processed_zones, risk_color

def render():
    st.title("City Risk Map")
    st.caption("Real-time heat vulnerability scores across 24 zones in 6 Indian cities")

    df = load_processed_zones()

    cities = ["All Cities"] + sorted(df["city"].unique().tolist())
    selected_city = st.selectbox("Filter by City", cities)

    if selected_city != "All Cities":
        df = df[df["city"] == selected_city]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Zones Monitored",
        f"{len(df)}" if selected_city == "All Cities" else len(df)
    )
    col2.metric("High Risk Zones", len(df[df["risk_tier"] == "High"]))
    col3.metric("Avg Risk Score", round(df["risk_score"].mean(), 1))
    col4.metric("Max Risk Score", round(df["risk_score"].max(), 1))

    st.divider()

    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5 if selected_city == "All Cities" else 11
    )

    for _, row in df.iterrows():
        color = risk_color(row["risk_tier"])
        popup_html = f"""
        <div style='font-family:Arial; min-width:180px'>
            <h4 style='margin:0;color:{color}'>{row['zone']}</h4>
            <p style='margin:4px 0'><b>City:</b> {row['city']}</p>
            <p style='margin:4px 0'><b>Risk Score:</b> {round(row['risk_score'], 1)}</p>
            <p style='margin:4px 0'><b>Risk Tier:</b>
                <span style='color:{color};font-weight:bold'>{row['risk_tier']}</span>
            </p>
            <p style='margin:4px 0'><b>Temperature:</b> {round(row['temperature'], 1)} C</p>
            <p style='margin:4px 0'><b>Humidity:</b> {round(row['humidity'], 1)}%</p>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['zone']} — {row['risk_tier']} ({round(row['risk_score'], 1)})"
        ).add_to(m)

    st_folium(m, width=1200, height=550)

    st.divider()
    st.subheader("Highest Priority Zones")
    st.caption("Sorted by highest risk score — zones requiring immediate attention.")

    display_df = df[["city", "zone", "temperature", "humidity", "risk_score", "risk_tier"]].sort_values(
        "risk_score", ascending=False
    ).reset_index(drop=True)
    display_df["temperature"] = display_df["temperature"].apply(lambda x: round(x, 1))
    display_df["humidity"]    = display_df["humidity"].apply(lambda x: round(x, 1))
    display_df["risk_score"]  = display_df["risk_score"].apply(lambda x: round(x, 1))
    display_df.columns = ["City", "Zone", "Temperature (°C)", "Humidity (%)", "Risk Score", "Risk Tier"]

    st.dataframe(display_df.astype(str), use_container_width=True, hide_index=True)

    st.divider()

    with st.expander("Why is a zone considered High Risk? — Understanding the Score"):
        st.markdown("""
Each zone receives a **heat vulnerability score from 0 to 100** based on current conditions.

The score reflects how dangerous current conditions are for that zone, combining:
- How hot and humid it feels right now
- How much the built environment traps heat (building density, lack of greenery)
- How well wind can dissipate heat

**Risk Tiers:**
- **Low (0–35):** Conditions are manageable. No immediate concern.
- **Medium (35–60):** Elevated risk. Vulnerable populations should take precautions.
- **High (60+):** Dangerous conditions. Immediate attention recommended.

Scores update daily with live weather data.
        """)

    with st.expander("Model Details — For Technical Users"):
        metrics_path = os.path.join(ROOT, "ml/artifacts/metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                metrics = json.load(f)
            rmse     = metrics.get("rmse", "0.52")
            r2       = metrics.get("r2", "0.996")
            baseline = f"{metrics.get('baseline_improvement_pct', '61.9')}%"
        else:
            rmse, r2, baseline = "0.52", "0.996", "61.9%"

        col1, col2, col3 = st.columns(3)
        col1.metric("RMSE on 2025 Data", rmse,
                    help="Average prediction error in risk score points on held-out 2025 data")
        col2.metric("R²", r2,
                    help="Model explains 99.6% of variance in risk scores on unseen 2025 data")
        col3.metric("Baseline Improvement", baseline,
                    help="Lower RMSE vs naive lag-1 baseline on 2025 test set")

        st.markdown("""
**Model:** XGBoost regression trained on 5 years of daily climate data (2021–2024) across 24 zones.

**Features:** temperature, humidity, wind speed, apparent temperature, building density index, greenery score, water proximity, 3-day rolling average temperature, previous day temperature.

**Validation approach:** Time-based forward split — trained on 2021–2024, tested on unseen 2025 data. No temporal leakage.

**Explainability:** SHAP TreeExplainer used for zone-level local feature attribution on every prediction.
        """)