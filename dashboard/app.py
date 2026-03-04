import streamlit as st
import sys
import os

#path setup
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="InfraUrban",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

#Bug fix:explicitly import from dashboard.utils
from dashboard.utils import get_last_updated, table_exists
from utils.pipeline import refresh

#cold-start guard: if DB is empty/missing, run the full pipeline once
if not table_exists("processed_zones"):
    with st.spinner("⚙️ First run — fetching live data & building DB (~30s)..."):
        try:
            refresh()
            st.success("✅ Data loaded! Dashboard is ready.")
        except Exception as e:
            st.error(f"❌ Pipeline failed on init: {e}")
            st.info("The dashboard may show empty charts. Try hitting Refresh below.")

#sidebar
st.sidebar.title("InfraUrban")
st.sidebar.caption("Urban Heat Intelligence Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["City Risk Map", "Zone Deep Dive", "Warming Trend Analysis", "Policy Simulator"]
)

st.sidebar.divider()

#refresh button
if st.sidebar.button(" Refresh Live Data", use_container_width=True):
    with st.spinner("Fetching live data... ~30 seconds"):
        try:
            refresh()
            st.sidebar.success(" Data refreshed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Refresh failed: {e}")

#Bug fix: get_last_updated is now null-safe, won't crash on empty DB
utc_time, ist_time = get_last_updated()
st.sidebar.caption("🕐 Data Last Updated")
st.sidebar.caption(f"UTC  —  {utc_time}")
st.sidebar.caption(f"IST   —  {ist_time}")

#page routing
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