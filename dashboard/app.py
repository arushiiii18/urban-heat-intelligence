import streamlit as st

st.set_page_config(
    page_title="InfraUrban",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dashboard.utils import get_last_updated

st.sidebar.title("InfraUrban")
st.sidebar.caption("Urban Heat Intelligence Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["City Risk Map", "Zone Deep Dive", "Warming Trend Analysis", "Policy Simulator"]
)

st.sidebar.divider()
utc_time, ist_time = get_last_updated()
st.sidebar.caption("Data Last Updated")
st.sidebar.caption(f"UTC  —  {utc_time}")
st.sidebar.caption(f"IST   —  {ist_time}")

st.sidebar.divider()
if st.sidebar.button("Refresh Live Data"):
    from utils.pipeline import refresh
    with st.sidebar:
        with st.spinner("Fetching latest data..."):
            refresh()
    st.sidebar.success("Data refreshed.")
    st.rerun()

if page == "City Risk Map":
    from dashboard.pages import city_map
    city_map.render()
elif page == "Zone Deep Dive":
    from dashboard.pages import zone_dive
    zone_dive.render()
elif page == "Warming Trend Analysis":
    from dashboard.pages import acceleration
    acceleration.render()
elif page == "Policy Simulator":
    from dashboard.pages import policy_simulator
    policy_simulator.render()