import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import shap
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from dashboard.utils import load_processed_zones, load_forecast, load_model, load_features

FEATURE_DISPLAY_NAMES = {
    "temperature":          "Temperature",
    "humidity":             "Humidity",
    "wind_speed":           "Wind Speed",
    "apparent_temperature": "Apparent Temperature",
    "building_density":     "Building Density Index",
    "greenery_score":       "Greenery Score",
    "water_distance":       "Water Proximity",
    "rolling_3day_temp":    "3-Day Avg Temp",
    "lag1_temp":            "Yesterday's Temp",
}

def render():
    st.title("Zone Deep Dive")
    st.caption("Understand what is driving risk in any monitored zone today")

    zones_df = load_processed_zones()
    forecast_df = load_forecast()

    col1, col2 = st.columns(2)
    with col1:
        selected_city = st.selectbox("Select City", sorted(zones_df["city"].unique().tolist()))
    with col2:
        city_zones = zones_df[zones_df["city"] == selected_city]["zone"].tolist()
        selected_zone = st.selectbox("Select Zone", city_zones)

    zone_data = zones_df[(zones_df["city"] == selected_city) & (zones_df["zone"] == selected_zone)].iloc[0]

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", round(zone_data["risk_score"], 1))
    col2.metric("Risk Tier", zone_data["risk_tier"])
    col3.metric("Temperature", f"{round(zone_data['temperature'], 1)} C")

    col4, col5, col6 = st.columns(3)
    col4.metric("Humidity", f"{round(zone_data['humidity'], 1)}%")
    col5.metric(
        "Wind Speed",
        f"{round(zone_data['wind_speed'], 1)} km/h",
        help="Higher wind speed helps dissipate heat and lowers risk."
    )
    col6.metric(
        "Building Density Index",
        round(zone_data["building_density"], 1),
        help="Normalized index derived from building count within 3km radius via OpenStreetMap. Higher value means denser built environment and greater heat retention."
    )

    col7, col8, col9 = st.columns(3)
    col7.metric(
        "Greenery Score",
        round(zone_data["greenery_score"], 2),
        help="Derived from vegetation and park coverage within 3km radius. Higher score means more natural cooling capacity."
    )
    col8.metric("Apparent Temperature", f"{round(zone_data['apparent_temperature'], 1)} C",
                help="Feels-like temperature accounting for humidity and wind. More representative of actual heat stress than raw temperature.")
    col9.metric("Water Proximity",
                round(zone_data["water_distance"], 3),
                help="Proximity to nearest water body in degrees. Closer water bodies contribute to humidity and moderate temperature extremes.")

    st.divider()

    st.subheader("What’s driving risk in this zone")
    st.caption("These factors are pushing the risk score up or down today. This reflects conditions specific to this zone right now — not a general ranking of features.")

    model = load_model()
    features = load_features()

    zone_features = pd.DataFrame([{
        "temperature":          zone_data["temperature"],
        "humidity":             zone_data["humidity"],
        "wind_speed":           zone_data["wind_speed"],
        "apparent_temperature": zone_data["apparent_temperature"],
        "building_density":     zone_data["building_density"],
        "greenery_score":       zone_data["greenery_score"],
        "water_distance":       zone_data["water_distance"],
        "rolling_3day_temp":    zone_data["rolling_3day_temp"],
        "lag1_temp":            zone_data["lag1_temp"],
    }])[features]

    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(zone_features)[0]

    display_names = [FEATURE_DISPLAY_NAMES.get(f, f) for f in features]

    shap_df = pd.DataFrame({
        "feature":    display_names,
        "shap_value": shap_values
    }).sort_values("shap_value", ascending=True)

    colors = ["#e74c3c" if v > 0 else "#27ae60" for v in shap_df["shap_value"]]

    fig_shap = go.Figure(go.Bar(
        x=shap_df["shap_value"],
        y=shap_df["feature"],
        orientation="h",
        marker_color=colors
    ))
    fig_shap.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis_title="Contribution to risk score",
        height=350,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_shap, use_container_width=True)
    st.caption("Red bars indicate this zone's feature value is pushing risk above the model's average expectation. Green bars indicate it is pulling risk below average. This is a local explanation specific to this zone's current conditions.")
    st.divider()

    st.subheader("7-Day Risk Forecast")
    st.caption("Predicted risk scores for the next 7 days based on weather forecast data passed through the trained model.")

    zone_forecast = forecast_df[
        (forecast_df["city"] == selected_city) &
        (forecast_df["zone"] == selected_zone)
    ].sort_values("forecast_date")

    if len(zone_forecast) > 0:
        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(
            x=zone_forecast["forecast_date"],
            y=zone_forecast["predicted_risk"].round(1),
            mode="lines+markers",
            line=dict(color="#e67e22", width=2),
            marker=dict(size=8),
            name="Predicted Risk"
        ))
        fig_forecast.add_hline(y=60, line_dash="dash", line_color="#e74c3c", annotation_text="High Risk Threshold")
        fig_forecast.add_hline(y=35, line_dash="dash", line_color="#27ae60", annotation_text="Low Risk Threshold")
        fig_forecast.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            yaxis=dict(range=[0, 100], title="Predicted Risk Score"),
            xaxis_title="Date",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
        st.caption("Short-term variability is expected to remain within the current risk band. Significant shifts would require sustained changes in temperature or humidity over multiple days.")
    else:
        st.warning("No forecast data available for this zone.")