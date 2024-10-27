import streamlit as st
from utils import init_session_state
from ui_components import (
    render_header,
    render_device_scanner,
    render_device_selector,
    render_connected_device
)

def main():
    # Initialize session state
    init_session_state()
    
    # Set page config
    st.set_page_config(
        page_title="SimpleTownBike",
        page_icon="🚴",
        layout="wide"
    )
    
    # Render UI components
    render_header()
    
    # Main content
    if not st.session_state.connected_device:
        render_device_scanner()
        render_device_selector()
    else:
        render_connected_device()
    
    # Footer
    st.markdown("---")
    st.markdown("*SimpleTownBike - Connect your fitness devices with ease*")

if __name__ == "__main__":
    main()
