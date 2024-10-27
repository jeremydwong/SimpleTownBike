import streamlit as st
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List

def format_timestamp(timestamp: str) -> str:
    """Convert timestamp string to readable format."""
    try:
        dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
        return dt.strftime('%B %d, %Y %I:%M %p')
    except ValueError:
        return timestamp

def calculate_workout_summary(workout_data: Dict) -> Dict:
    """Calculate summary statistics for a workout."""
    summary = {}
    metrics = workout_data.get('metrics', {})
    
    # Calculate averages and maximums for each metric
    for metric_name, metric_data in metrics.items():
        if metric_name == 'distance':
            # Convert distance to kilometers
            max_distance = max(metric_data['values'], default=0) / 1000
            summary['distance'] = f"{max_distance:.2f} km"
        elif metric_name not in ['timestamps']:
            values = metric_data['values']
            if values:
                avg_value = sum(values) / len(values)
                max_value = max(values)
                
                # Format values based on metric type
                if metric_name == 'speed':
                    summary[f'avg_{metric_name}'] = f"{avg_value:.1f} km/h"
                    summary[f'max_{metric_name}'] = f"{max_value:.1f} km/h"
                else:
                    summary[f'avg_{metric_name}'] = f"{int(avg_value)} {get_metric_unit(metric_name)}"
                    summary[f'max_{metric_name}'] = f"{int(max_value)} {get_metric_unit(metric_name)}"
    
    # Calculate duration
    if metrics and metrics.get('heart_rate', {}).get('timestamps'):
        timestamps = metrics['heart_rate']['timestamps']
        duration_seconds = max(timestamps) - min(timestamps)
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        summary['duration'] = f"{minutes:02d}:{seconds:02d}"
    else:
        summary['duration'] = "00:00"
    
    return summary

def get_metric_unit(metric_name: str) -> str:
    """Get the unit for a given metric."""
    units = {
        'heart_rate': 'bpm',
        'power': 'W',
        'cadence': 'rpm',
        'speed': 'km/h',
        'resistance': ''
    }
    return units.get(metric_name, '')

def render_workout_history():
    """Render the workout history section."""
    if not st.session_state.storage_manager.is_authenticated():
        st.warning("⚠️ Connect to Dropbox to view workout history.")
        return
    
    st.header("Workout History")
    
    # Get list of workouts
    workouts = st.session_state.storage_manager.list_workouts()
    
    if not workouts:
        st.info("No workout history found. Complete a workout and save it to see it here!")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Summary View", "Detailed Analysis"])
    
    with tab1:
        # Display workout summaries in a grid
        for i in range(0, len(workouts), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(workouts):
                    workout = workouts[i + j]
                    with cols[j]:
                        with st.expander(format_timestamp(workout['name'].split('_')[1].split('.')[0])):
                            workout_data = st.session_state.storage_manager.get_workout(workout['path'])
                            if workout_data:
                                summary = calculate_workout_summary(workout_data)
                                st.markdown("**Duration:** " + summary['duration'])
                                if 'distance' in summary:
                                    st.markdown("**Distance:** " + summary['distance'])
                                if 'avg_heart_rate' in summary:
                                    st.markdown("**Avg Heart Rate:** " + summary['avg_heart_rate'])
                                if 'avg_power' in summary:
                                    st.markdown("**Avg Power:** " + summary['avg_power'])
                                if 'avg_cadence' in summary:
                                    st.markdown("**Avg Cadence:** " + summary['avg_cadence'])
                            else:
                                st.error("Error loading workout data")
    
    with tab2:
        # Select workout for detailed analysis
        selected_workout = st.selectbox(
            "Select Workout",
            options=workouts,
            format_func=lambda x: format_timestamp(x['name'].split('_')[1].split('.')[0])
        )
        
        if selected_workout:
            workout_data = st.session_state.storage_manager.get_workout(selected_workout['path'])
            if workout_data:
                # Create detailed visualizations
                metrics = workout_data.get('metrics', {})
                if metrics:
                    for metric_name, metric_data in metrics.items():
                        if metric_name not in ['timestamps']:
                            # Create DataFrame for the metric
                            df = pd.DataFrame({
                                'timestamp': pd.to_datetime(metric_data['timestamps'], unit='s'),
                                'value': metric_data['values']
                            })
                            
                            # Plot the metric
                            st.subheader(f"{metric_name.replace('_', ' ').title()}")
                            st.line_chart(df.set_index('timestamp'))
            else:
                st.error("Error loading workout data")

def render_current_session_controls():
    """Render controls for the current workout session."""
    if st.session_state.connected_device:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Session Controls")
        
        # Save workout button with confirmation
        if st.sidebar.button("End & Save Workout"):
            if st.session_state.storage_manager.is_authenticated():
                success = st.session_state.storage_manager.save_workout_data(
                    st.session_state.ble_manager.get_metrics_data()
                )
                if success:
                    st.sidebar.success("Workout saved successfully!")
                    # Clear current session data
                    for metric in st.session_state.ble_manager.metrics:
                        st.session_state.ble_manager.metrics[metric]['values'] = []
                        st.session_state.ble_manager.metrics[metric]['timestamps'] = []
                else:
                    st.sidebar.error("Failed to save workout")
            else:
                st.sidebar.error("Dropbox connection required to save workouts")
