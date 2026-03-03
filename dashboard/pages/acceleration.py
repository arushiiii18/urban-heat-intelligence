import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from dashboard.utils import load_acceleration, load_processed_zones

def render():
    st.title("Warming Trend Analysis")
    st.caption("Zones where average annual temperature has been rising at a statistically notable rate over the past 5 years")

    df = load_acceleration()
    zones_df = load_processed_zones()

    df = df.merge(zones_df[["city", "zone", "risk_score", "risk_tier"]], on=["city", "zone"], how="left")

    accelerating = df[df["is_accelerating"] == 1]
    high_risk_accelerating = accelerating[accelerating["risk_score"] >= 35]

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Zones Tracked", len(df))
    col2.metric("Accelerating Zones", int(df["is_accelerating"].sum()))
    col3.metric("Fastest Warming Zone", df.sort_values("slope", ascending=False).iloc[0]["zone"])

    st.divider()

    st.info(
        f"{int(df['is_accelerating'].sum())} zones show a statistically significant upward warming trend. "
        f"All of them currently carry medium or above risk scores — "
        f"these represent the highest structural priority for long-term intervention."
    )

    st.divider()

    st.subheader("Warming Rate vs Current Risk Score")
    st.caption(
        "Zones positioned toward the top-right are both currently high-risk and warming fastest — "
        "highest priority for infrastructure planning. "
        "Accelerating zones are those with a statistically significant positive warming slope "
        "(top 20% of observed slopes across all monitored zones)."
    )

    df["status"] = df["is_accelerating"].apply(lambda x: "Accelerating" if x == 1 else "Stable")

    fig = go.Figure()
    for status, color in [("Accelerating", "#e74c3c"), ("Stable", "#7f8c8d")]:
        subset = df[df["status"] == status]
        fig.add_trace(go.Scatter(
            x=subset["slope"],
            y=subset["risk_score"].round(1),
            mode="markers+text",
            name=status,
            text=subset["zone"],
            textposition="top center",
            textfont=dict(size=10, color="white"),
            marker=dict(size=14, color=color, line=dict(width=1, color="white"))
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis=dict(title="Warming Rate (°C per year)", gridcolor="#2c2c2c"),
        yaxis=dict(title="Current Risk Score", gridcolor="#2c2c2c"),
        height=500,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Zone Warming Rankings")
    st.caption("Slope = °C increase per year averaged over 2021–2025. R-squared indicates how consistent the trend is. P-value below 0.05 indicates statistical significance.")

    display_df = df[["city", "zone", "slope", "r_squared", "p_value", "is_accelerating", "risk_score", "risk_tier"]].sort_values("slope", ascending=False).reset_index(drop=True)
    display_df["is_accelerating"] = display_df["is_accelerating"].apply(lambda x: "Yes" if x == 1 else "No")
    display_df["slope"]           = display_df["slope"].apply(lambda x: round(x, 3))
    display_df["r_squared"]       = display_df["r_squared"].apply(lambda x: round(x, 3))
    display_df["p_value"]         = display_df["p_value"].apply(lambda x: round(x, 3))
    display_df["risk_score"]      = display_df["risk_score"].apply(lambda x: round(x, 1))
    display_df.columns = ["City", "Zone", "Slope (°C/yr)", "R-Squared", "P-Value", "Accelerating", "Risk Score", "Risk Tier"]

    st.dataframe(display_df.astype(str), use_container_width=True, hide_index=True)