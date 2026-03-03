import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from dashboard.utils import load_processed_zones, classify_risk

def formula_score(row):
    temp_score     = min((row["temperature"] / 45) * 40, 40)
    humidity_score = min((row["humidity"] / 100) * 20, 20)
    building_score = min((row["building_density"] / 60) * 20, 20)
    greenery_score = max(0, 10 - (row["greenery_score"] * 2))
    wind_score     = max(0, 10 - (row["wind_speed"] * 2))
    return round(temp_score + humidity_score + building_score + greenery_score + wind_score, 2)

def render():
    st.title("Policy Simulator")
    st.caption("Model the impact of infrastructure interventions on heat vulnerability before committing to policy decisions")

    zones_df = load_processed_zones()

    col1, col2 = st.columns(2)
    with col1:
        selected_city = st.selectbox("Select City", sorted(zones_df["city"].unique().tolist()))
    with col2:
        city_zones = zones_df[zones_df["city"] == selected_city]["zone"].tolist()
        selected_zone = st.selectbox("Select Zone", city_zones)

    zone_data = zones_df[(zones_df["city"] == selected_city) & (zones_df["zone"] == selected_zone)].iloc[0]

    baseline_score = formula_score(zone_data)
    baseline_tier  = classify_risk(baseline_score)

    st.divider()

    st.subheader("Current Zone State")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score", round(baseline_score, 1))
    col2.metric("Risk Tier", baseline_tier)
    col3.metric(
        "Greenery Score",
        round(zone_data["greenery_score"], 2),
        help="Vegetation and park coverage index within 3km radius. Higher = more natural cooling."
    )
    col4.metric(
        "Building Density Index",
        round(zone_data["building_density"], 1),
        help="Normalized building count index within 3km radius. Higher = denser built environment = greater heat retention."
    )

    st.divider()

    st.subheader("Simulate Interventions")
    st.caption("Adjust sliders to model infrastructure changes. Temperature and humidity are climate-driven and cannot be directly intervened upon — combine multiple interventions for meaningful tier-level change.")

    col1, col2 = st.columns(2)
    with col1:
        greenery_increase = st.slider(
            "Increase Greenery Coverage (%)",
            min_value=0, max_value=100, value=0, step=5,
            help="Simulates adding parks, trees, green corridors to the zone"
        )
        building_reduction = st.slider(
            "Reduce Building Density (%)",
            min_value=0, max_value=50, value=0, step=5,
            help="Simulates density caps, demolition of excess structures, or open space creation"
        )
    with col2:
        wind_increase = st.slider(
            "Improve Wind Corridor (%)",
            min_value=0, max_value=50, value=0, step=5,
            help="Simulates urban layout changes that allow better airflow through the zone"
        )
        humidity_reduction = st.slider(
            "Reduce Humidity (%)",
            min_value=0, max_value=30, value=0, step=5,
            help="Simulates improved drainage and reduced surface water accumulation"
        )

    modified = {
        "temperature":      zone_data["temperature"],
        "humidity":         zone_data["humidity"] * (1 - humidity_reduction / 100),
        "wind_speed":       zone_data["wind_speed"] * (1 + wind_increase / 100),
        "building_density": zone_data["building_density"] * (1 - building_reduction / 100),
        "greenery_score":   zone_data["greenery_score"] * (1 + greenery_increase / 100),
    }

    new_score = formula_score(modified)
    new_tier  = classify_risk(new_score)
    delta     = round(baseline_score - new_score, 2)
    delta_pct = round((delta / baseline_score) * 100, 1) if baseline_score > 0 else 0

    st.divider()

    st.subheader("Projected Outcome")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Original Risk Score", round(baseline_score, 1))
    any_intervention = (greenery_increase + building_reduction + wind_increase + humidity_reduction) > 0
    col2.metric(
        "Projected Risk Score",
        round(new_score, 1),
        delta=f"-{delta}" if delta > 0 else f"+{abs(delta)}" if any_intervention else None,
        delta_color="inverse"
    )
    col3.metric("Risk Reduction", f"{delta} pts")
    col4.metric("Percentage Reduction", f"{delta_pct}%")

    fig = go.Figure()
    for label, value, color in [
        ("Before Intervention", baseline_score, "#e74c3c" if baseline_score >= 60 else "#e67e22"),
        ("After Intervention",  new_score,      "#27ae60" if new_score < 35 else "#e67e22" if new_score < 60 else "#e74c3c")
    ]:
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=round(value, 1),
            title={"text": label, "font": {"color": "white", "size": 14}},
            domain={"row": 0, "column": 0 if label == "Before Intervention" else 1},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 35],  "color": "#1e3a2f"},
                    {"range": [35, 60], "color": "#3a2a0a"},
                    {"range": [60, 100],"color": "#3a0a0a"},
                ]
            }
        ))

    fig.update_layout(
        grid={"rows": 1, "columns": 2, "pattern": "independent"},
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Intervention Summary")
    summary_data = {
        "Intervention": ["Greenery Increase", "Building Density Reduction", "Wind Corridor Improvement", "Humidity Reduction"],
        "Applied":      [f"+{greenery_increase}%", f"-{building_reduction}%", f"+{wind_increase}%", f"-{humidity_reduction}%"],
        "Status":       ["Active" if v > 0 else "Not Applied" for v in [greenery_increase, building_reduction, wind_increase, humidity_reduction]]
    }
    st.dataframe(pd.DataFrame(summary_data).astype(str), use_container_width=True, hide_index=True)

    st.divider()

    if delta <= 0 and (greenery_increase + building_reduction + wind_increase + humidity_reduction) == 0:
        st.info("No interventions applied. Adjust the sliders above to model the effect of infrastructure changes on this zone.")
    elif delta <= 0:
        st.warning("Current settings are not producing a risk reduction. Try increasing greenery coverage or reducing building density for more impact.")
    elif delta_pct >= 15:
        tier_change = f"Risk tier shifts from {baseline_tier} to {new_tier}." if new_tier != baseline_tier else f"Risk tier remains {baseline_tier} — additional intervention needed to cross the next threshold."
        st.success(f"High-impact intervention. Projected risk reduction of {delta_pct}% ({delta} pts). {tier_change}")
    elif delta_pct >= 5:
        tier_change = f"Risk tier shifts from {baseline_tier} to {new_tier}." if new_tier != baseline_tier else f"Risk tier remains {baseline_tier} — meaningful reduction but tier threshold not yet crossed."
        st.warning(f"Moderate intervention impact. Projected reduction of {delta_pct}% ({delta} pts). {tier_change}")
    else:
        st.warning(f"Minor impact detected. Projected reduction of {delta_pct}% ({delta} pts). Risk tier remains {baseline_tier}. Consider combining multiple interventions for stronger effect.")