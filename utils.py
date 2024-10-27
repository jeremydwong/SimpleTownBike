import asyncio
from typing import Callable, Any
import streamlit as st

def run_async(func: Callable) -> Any:
    """Helper function to run async functions in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func())
    loop.close()
    return result

def init_session_state():
    """Initialize session state variables."""
    if 'ble_manager' not in st.session_state:
        from ble_manager import BLEManager
        st.session_state.ble_manager = BLEManager()
    
    if 'connected_device' not in st.session_state:
        st.session_state.connected_device = None
    
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    
    if 'devices' not in st.session_state:
        st.session_state.devices = []

def format_device_name(device: dict) -> str:
    """Format device name for display in dropdown."""
    return f"{device['name']} ({device['address']}) - Signal: {device['rssi']} dBm"
