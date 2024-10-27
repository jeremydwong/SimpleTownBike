import streamlit as st
from utils import init_session_state
from ui_components import (
    render_header,
    render_device_scanner,
    render_device_selector,
    render_connected_device,
    render_environment_info
)
from target_settings import render_target_settings
from storage_manager import StorageManager

def init_storage_manager():
    """Initialize storage manager in session state if not present."""
    if 'storage_manager' not in st.session_state:
        st.session_state.storage_manager = StorageManager()

def save_current_workout():
    """Save current workout data to Dropbox."""
    if st.session_state.ble_manager.get_metrics_data():
        success = st.session_state.storage_manager.save_workout_data(
            st.session_state.ble_manager.get_metrics_data()
        )
        if success:
            st.success("Workout data saved successfully!")
        else:
            st.error("Failed to save workout data. Please try again.")

def main():
    # Initialize session state
    init_session_state()
    init_storage_manager()
    
    # Set page config
    st.set_page_config(
        page_title="SimpleTownBike",
        page_icon="🚴",
        layout="wide"
    )
    
    # Render UI components
    render_header()
    render_environment_info()
    
    # Main content
    if not st.session_state.connected_device:
        render_device_scanner()
        render_device_selector()
    else:
        # Render target settings in sidebar when device is connected
        render_target_settings()
        render_connected_device()
        
        # Add save workout button
        if st.button("Save Workout Data"):
            save_current_workout()
    
    # Footer
    st.markdown("---")
    st.markdown("*SimpleTownBike - Connect your fitness devices with ease*")

if __name__ == "__main__":
    main()
