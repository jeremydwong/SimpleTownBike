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
from workout_manager import render_workout_history, render_current_session_controls

def init_storage_manager():
    """Initialize storage manager in session state if not present."""
    if 'storage_manager' not in st.session_state:
        st.session_state.storage_manager = StorageManager()
        if not st.session_state.storage_manager.is_authenticated():
            st.error("⚠️ Failed to authenticate with Dropbox. Please check your access token.")
            st.info("Your workout data will not be saved until the Dropbox connection is fixed.")

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
        # Show device connection interface and workout history
        col1, col2 = st.columns([1, 2])
        with col1:
            render_device_scanner()
            render_device_selector()
        with col2:
            render_workout_history()
    else:
        # Render target settings and session controls in sidebar
        render_target_settings()
        render_current_session_controls()
        
        # Show connected device interface and metrics
        render_connected_device()
        
        # Show workout history below the metrics
        st.markdown("---")
        render_workout_history()
    
    # Footer
    st.markdown("---")
    st.markdown("*SimpleTownBike - Connect your fitness devices with ease*")

if __name__ == "__main__":
    main()
