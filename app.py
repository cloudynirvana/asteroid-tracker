"""Streamlit dashboard: which asteroids pass Earth in the coming days?

Run with:  streamlit run app.py
"""
from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from neows import fetch_range

st.set_page_config(page_title="Asteroid tracker", page_icon="☄️", layout="wide")
st.title("☄️ Asteroids passing Earth")
st.caption("Data: NASA Near Earth Object Web Service (NeoWs), via api.nasa.gov.")

today = date.today()
with st.sidebar:
    st.header("Options")
    picked = st.date_input("Date range", (today, today + timedelta(days=6)))
    hazardous_only = st.toggle("Only potentially hazardous", value=False)
    st.markdown(
        "**What \"potentially hazardous\" means:** an object at least about 140 m "
        "across whose orbit comes within 7.5 million km of Earth's orbit. It is a "
        "label for objects worth watching, **not a prediction that anything will hit us.**"
    )

if not isinstance(picked, tuple) or len(picked) != 2:
    st.info("Pick an end date to load data.")
    st.stop()
start, end = picked
if (end - start).days > 92:
    st.warning("Please pick a range of three months or less.")
    st.stop()


@st.cache_data(ttl=3600, show_spinner="Asking NASA...")
def load(a, b):
    return fetch_range(a, b)


try:
    df = load(start, end)
except Exception as e:  # show the reason instead of a stack trace
    st.error(f"Could not load data: {e}")
    st.stop()

if hazardous_only:
    df = df[df.hazardous]
if df.empty:
    st.info("No asteroids match these options. Try a wider date range.")
    st.stop()

closest = df.loc[df.lunar_distances.idxmin()]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Close approaches", f"{len(df)}")
c2.metric("Potentially hazardous", f"{int(df.hazardous.sum())}")
c3.metric("Closest pass (lunar distances)", f"{closest.lunar_distances:.1f}", closest["name"], delta_color="off")
c4.metric("Largest (upper estimate)", f"{df.diameter_max_m.max():,.0f} m")

st.subheader("Size against distance")
st.caption(
    "Each bar spans NASA's minimum to maximum size estimate. Sizes are worked out "
    "from how bright an object looks, so NASA gives a range, not one number. "
    "1 lunar distance = 384,400 km, the distance from Earth to the Moon."
)
mid = (df.diameter_min_m + df.diameter_max_m) / 2
fig = go.Figure()
for flag, colour, label in [(False, "#4e79a7", "Not flagged"), (True, "#e15759", "Potentially hazardous")]:
    part = df[df.hazardous == flag]
    if part.empty:
        continue
    m = mid[part.index]
    fig.add_trace(go.Scatter(
        x=part.lunar_distances, y=m, mode="markers", name=label,
        marker=dict(color=colour, size=8),
        error_y=dict(type="data", symmetric=False,
                     array=part.diameter_max_m - m, arrayminus=m - part.diameter_min_m,
                     thickness=1, width=0),
        customdata=part[["name", "diameter_min_m", "diameter_max_m", "speed_kmh", "approach_date"]],
        hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[4]|%d %b %Y}<br>"
                       "%{x:.2f} lunar distances<br>"
                       "%{customdata[1]:,.0f} to %{customdata[2]:,.0f} m across<br>"
                       "%{customdata[3]:,.0f} km/h<extra></extra>"),
    ))
fig.update_layout(
    xaxis_title="Miss distance (lunar distances, log scale)", xaxis_type="log",
    yaxis_title="Estimated diameter (m, log scale)", yaxis_type="log",
    height=500, margin=dict(t=10), legend=dict(orientation="h", y=1.05),
)
st.plotly_chart(fig, width="stretch")

st.subheader("All close approaches, largest first")
table = df.assign(
    approach_date=df.approach_date.dt.date,
    miss_km=df.miss_km.round(0),
    speed_kmh=df.speed_kmh.round(0),
)[["name", "approach_date", "diameter_min_m", "diameter_max_m",
   "lunar_distances", "miss_km", "speed_kmh", "hazardous", "jpl_url"]]
st.dataframe(
    table, hide_index=True, width="stretch",
    column_config={
        "name": "Name",
        "approach_date": "Closest approach",
        "diameter_min_m": st.column_config.NumberColumn("Min size (m)", format="%.0f"),
        "diameter_max_m": st.column_config.NumberColumn("Max size (m)", format="%.0f"),
        "lunar_distances": st.column_config.NumberColumn("Miss distance (lunar distances)", format="%.2f"),
        "miss_km": st.column_config.NumberColumn("Miss distance (km)", format="%,.0f"),
        "speed_kmh": st.column_config.NumberColumn("Speed (km/h)", format="%,.0f"),
        "hazardous": "Potentially hazardous",
        "jpl_url": st.column_config.LinkColumn("JPL page", display_text="details"),
    },
)
