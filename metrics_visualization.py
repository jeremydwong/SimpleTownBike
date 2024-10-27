import streamlit as st
import numpy as np
import time
from typing import Dict, List
import pandas as pd

def is_within_target(value: float, metric: str) -> tuple:
    """Check if value is within target range and return status and color."""
    if not st.session_state.get('targets', {}).get(metric, {}).get('enabled', False):
        return None, None
    
    targets = st.session_state.targets[metric]
    if value < targets['min']:
        return "Below Target", "red"
    elif value > targets['max']:
        return "Above Target", "red"
    return "On Target", "green"

def create_metric_chart(values: List[float], timestamps: List[float], 
                     min_val: float, max_val: float, unit: str, metric_name: str):
    """Create a line chart for a specific metric."""
    if not values or not timestamps:
        return None

    # Create DataFrame for the metric
    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': values
    })
    
    # Convert timestamps to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    # Create the chart
    chart = st.line_chart(df)
    
    # Add target range indicators if enabled
    if st.session_state.get('targets', {}).get(metric_name, {}).get('enabled', False):
        targets = st.session_state.targets[metric_name]
        st.caption(f"Target Range: {targets['min']} - {targets['max']} {unit}")
    
    return chart

def render_metrics_dashboard(metrics: Dict):
    """Render the metrics dashboard with real-time plots."""
    if not metrics:
        return

    st.subheader("Real-time Metrics")
    
    # Create three columns for primary metrics
    col1, col2, col3 = st.columns(3)
    
    # Heart Rate
    with col1:
        current_hr = int(metrics['heart_rate']['values'][-1]) if metrics['heart_rate']['values'] else 0
        status, color = is_within_target(current_hr, 'heart_rate')
        
        metric_container = st.container()
        with metric_container:
            st.metric(
                "Heart Rate",
                f"{current_hr} bpm",
                delta=status,
                delta_color="off" if not status else "normal"
            )
            if status:
                st.markdown(f"<p style='color: {color}'>{status}</p>", unsafe_allow_html=True)
                
        create_metric_chart(
            metrics['heart_rate']['values'],
            metrics['heart_rate']['timestamps'],
            60, 200, "bpm", "heart_rate"
        )
    
    # Power
    with col2:
        current_power = int(metrics['power']['values'][-1]) if metrics['power']['values'] else 0
        avg_power = int(metrics['avg_power']['values'][-1]) if metrics['avg_power']['values'] else 0
        status, color = is_within_target(current_power, 'power')
        
        metric_container = st.container()
        with metric_container:
            st.metric(
                "Power",
                f"{current_power} W",
                delta=status if status else f"Avg: {avg_power} W",
                delta_color="off" if not status else "normal"
            )
            if status:
                st.markdown(f"<p style='color: {color}'>{status}</p>", unsafe_allow_html=True)
                
        create_metric_chart(
            metrics['power']['values'],
            metrics['power']['timestamps'],
            0, 400, "W", "power"
        )
    
    # Cadence
    with col3:
        current_cadence = int(metrics['cadence']['values'][-1]) if metrics['cadence']['values'] else 0
        avg_cadence = int(metrics['avg_cadence']['values'][-1]) if metrics['avg_cadence']['values'] else 0
        status, color = is_within_target(current_cadence, 'cadence')
        
        metric_container = st.container()
        with metric_container:
            st.metric(
                "Cadence",
                f"{current_cadence} rpm",
                delta=status if status else f"Avg: {avg_cadence} rpm",
                delta_color="off" if not status else "normal"
            )
            if status:
                st.markdown(f"<p style='color: {color}'>{status}</p>", unsafe_allow_html=True)
                
        create_metric_chart(
            metrics['cadence']['values'],
            metrics['cadence']['timestamps'],
            0, 120, "rpm", "cadence"
        )

    # Create three columns for secondary metrics
    st.subheader("Additional Metrics")
    col4, col5, col6 = st.columns(3)

    # Speed
    with col4:
        current_speed = round(metrics['speed']['values'][-1], 1) if metrics['speed']['values'] else 0
        avg_speed = round(metrics['avg_speed']['values'][-1], 1) if metrics['avg_speed']['values'] else 0
        status, color = is_within_target(current_speed, 'speed')
        
        metric_container = st.container()
        with metric_container:
            st.metric(
                "Speed",
                f"{current_speed} km/h",
                delta=status if status else f"Avg: {avg_speed} km/h",
                delta_color="off" if not status else "normal"
            )
            if status:
                st.markdown(f"<p style='color: {color}'>{status}</p>", unsafe_allow_html=True)
                
        create_metric_chart(
            metrics['speed']['values'],
            metrics['speed']['timestamps'],
            0, 50, "km/h", "speed"
        )

    # Distance
    with col5:
        distance = round(metrics['distance']['values'][-1]/1000, 2) if metrics['distance']['values'] else 0
        st.metric(
            "Distance",
            f"{distance} km",
            delta=None
        )
        create_metric_chart(
            metrics['distance']['values'],
            metrics['distance']['timestamps'],
            0, None, "m", "distance"
        )

    # Resistance
    with col6:
        resistance = int(metrics['resistance']['values'][-1]) if metrics['resistance']['values'] else 0
        status, color = is_within_target(resistance, 'resistance')
        
        metric_container = st.container()
        with metric_container:
            st.metric(
                "Resistance Level",
                str(resistance),
                delta=status,
                delta_color="off" if not status else "normal"
            )
            if status:
                st.markdown(f"<p style='color: {color}'>{status}</p>", unsafe_allow_html=True)
                
        create_metric_chart(
            metrics['resistance']['values'],
            metrics['resistance']['timestamps'],
            1, 20, "level", "resistance"
        )
