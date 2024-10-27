import streamlit as st
import numpy as np
import time
from typing import Dict, List
import pandas as pd

def create_metric_chart(title: str, values: List[float], timestamps: List[float], 
                       min_val: float, max_val: float, unit: str):
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
    
    return chart

def render_metrics_dashboard(metrics: Dict):
    """Render the metrics dashboard with real-time plots."""
    if not metrics:
        return

    st.subheader("Real-time Metrics")
    
    # Create three columns for the metrics
    col1, col2, col3 = st.columns(3)
    
    # Heart Rate
    with col1:
        st.metric(
            "Heart Rate",
            f"{int(metrics['heart_rate']['values'][-1]) if metrics['heart_rate']['values'] else 0} bpm",
            delta=None
        )
        create_metric_chart(
            "Heart Rate",
            metrics['heart_rate']['values'],
            metrics['heart_rate']['timestamps'],
            60, 200, "bpm"
        )
    
    # Power
    with col2:
        st.metric(
            "Power",
            f"{int(metrics['power']['values'][-1]) if metrics['power']['values'] else 0} W",
            delta=None
        )
        create_metric_chart(
            "Power",
            metrics['power']['values'],
            metrics['power']['timestamps'],
            0, 400, "W"
        )
    
    # Cadence
    with col3:
        st.metric(
            "Cadence",
            f"{int(metrics['cadence']['values'][-1]) if metrics['cadence']['values'] else 0} rpm",
            delta=None
        )
        create_metric_chart(
            "Cadence",
            metrics['cadence']['values'],
            metrics['cadence']['timestamps'],
            0, 120, "rpm"
        )
