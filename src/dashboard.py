import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Configure page layout and title
st.set_page_config(
    page_title="Space Weather Operational Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Load cleaned NASA OMNI2 observations with caching for instant loading
@st.cache_data
def load_data():
    file_path = Path("data/processed/omni2_cleaned.csv")
    if not file_path.exists():
        file_path = Path("../data/processed/omni2_cleaned.csv")
    
    data = pd.read_csv(file_path, parse_dates=["Timestamp"], index_col="Timestamp")
    return data

df = load_data()

# 2. Main Title Banner
st.title("NASA OMNI2 Space Weather Monitoring & Disturbance Center")
st.markdown(
    "**Multi-Spacecraft Interplanetary Observation Analysis (2018–2023)** | "
    "Supervised 1-Hour Ahead Geomagnetic Storm Forecasting"
)
st.write("---")

# 3. Sidebar Controls
st.sidebar.header("Dashboard Controls & Filters")
st.sidebar.markdown("Filter observations and inspect specific geomagnetic disturbance periods:")

# Date picker
min_date = df.index.min().date()
max_date = df.index.max().date()

selected_dates = st.sidebar.date_input(
    "Select Observation Window:",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Quick navigation buttons for major space physics events
st.sidebar.markdown("### Significant Event Presets")
if st.sidebar.button("Focus: March 2023 G4 Storm (-213 nT)"):
    selected_dates = [pd.to_datetime("2023-03-22").date(), pd.to_datetime("2023-03-26").date()]

# Filter dataframe based on date range
if len(selected_dates) == 2:
    start_dt = pd.to_datetime(selected_dates[0])
    end_dt = pd.to_datetime(selected_dates[1]) + pd.Timedelta(days=1)
    df_filtered = df.loc[start_dt:end_dt]
else:
    df_filtered = df

# 4. Top Executive KPI Scorecards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(label="Total Hours Monitored", value=f"{len(df_filtered):,}")

with kpi2:
    avg_speed = df_filtered["Flow_Speed"].mean()
    st.metric(label="Avg Solar Wind Velocity", value=f"{avg_speed:.1f} km/s")

with kpi3:
    avg_b = df_filtered["Scalar_B"].mean()
    st.metric(label="Avg Interplanetary B Field", value=f"{avg_b:.2f} nT")

with kpi4:
    min_dst = df_filtered["Dst_index"].min()
    st.metric(label="Peak Storm Minimum (Dst)", value=f"{min_dst:.0f} nT")

st.write("---")

# 5. Operational Multi-Tab Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "Geomagnetic Dst Timeline", 
    "Solar Wind Dynamics", 
    "Magnetic Reconnection (Bz)", 
    "Severe Storm Catalog"
])

# TAB 1: Dst Timeline with Scientific Storm Thresholds
with tab1:
    st.subheader("Terrestrial Ring Current Disturbance (Dst Index)")
    st.caption("Dashed lines indicate scientific storm classifications: Moderate (-50 nT) and Intense (-100 nT).")
    
    fig_dst = go.Figure()
    fig_dst.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["Dst_index"],
        mode="lines",
        name="Dst Index",
        line=dict(color="#d62728", width=1.5)
    ))
    fig_dst.add_hline(y=-50, line_dash="dash", line_color="orange", annotation_text="Moderate Storm (-50 nT)")
    fig_dst.add_hline(y=-100, line_dash="dash", line_color="red", annotation_text="Intense Storm (-100 nT)")
    fig_dst.update_layout(
        xaxis_title="Observation Timestamp (UTC)",
        yaxis_title="Dst Index [nT]",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=20, b=40),
        height=450
    )
    st.plotly_chart(fig_dst, use_container_width=True)

# TAB 2: Solar Wind & Plasma Dynamics
with tab2:
    st.subheader("Solar Wind Flow Velocity & Dynamic Pressure")
    
    col_a, col_b = st.columns(2)
    with col_a:
        fig_speed = px.line(
            df_filtered, 
            x=df_filtered.index, 
            y="Flow_Speed", 
            title="Solar Wind Speed (km/s)",
            labels={"Flow_Speed": "Speed [km/s]", "index": "Timestamp"},
            color_discrete_sequence=["#ff7f0e"]
        )
        fig_speed.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_speed, use_container_width=True)

    with col_b:
        fig_press = px.line(
            df_filtered, 
            x=df_filtered.index, 
            y="Flow_Pressure", 
            title="Solar Wind Dynamic Pressure (nPa)",
            labels={"Flow_Pressure": "Pressure [nPa]", "index": "Timestamp"},
            color_discrete_sequence=["#2ca02c"]
        )
        fig_press.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_press, use_container_width=True)

# TAB 3: Magnetic Field Reconnection Coupling
with tab3:
    st.subheader("Interplanetary Magnetic Field Bz Coupling")
    st.caption("Prolonged southward excursions (Bz < 0) drive dayside magnetic reconnection, transferring kinetic energy to Earth.")
    
    fig_bz = px.line(
        df_filtered, 
        x=df_filtered.index, 
        y="BZ_GSM", 
        title="IMF Bz Component (GSM Coordinates) [nT]",
        labels={"BZ_GSM": "Bz [nT]", "index": "Timestamp"},
        color_discrete_sequence=["#1f77b4"]
    )
    fig_bz.add_hline(y=0, line_color="black", line_dash="solid")
    fig_bz.add_hline(y=-10, line_color="red", line_dash="dot", annotation_text="Strong Southward Threshold (-10 nT)")
    fig_bz.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_bz, use_container_width=True)
    
    # Scatter plot showing Bz vs Dst correlation
    fig_scatter = px.scatter(
        df_filtered.sample(min(3000, len(df_filtered))),
        x="BZ_GSM",
        y="Dst_index",
        color="Flow_Speed",
        title="Physical Coupling: IMF Bz vs Dst Response (Sampled, Colored by Solar Wind Speed)",
        labels={"BZ_GSM": "IMF Bz (GSM) [nT]", "Dst_index": "Dst Index [nT]", "Flow_Speed": "Speed [km/s]"},
        color_continuous_scale="Viridis",
        opacity=0.6
    )
    fig_scatter.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

# TAB 4: Severe Storm Catalog
with tab4:
    st.subheader("Severe Geomagnetic Storm Event Records (Dst <= -50 nT)")
    storms = df_filtered[df_filtered["Dst_index"] <= -50]
    
    st.write(f"Total Disturbed Storm Hours in Selected Range: **{len(storms):,} hours**")
    st.dataframe(
        storms[["Dst_index", "BZ_GSM", "Flow_Speed", "Proton_Density", "Flow_Pressure", "Electric_Field"]]
        .sort_values(by="Dst_index", ascending=True)
        .head(100),
        use_container_width=True
    )