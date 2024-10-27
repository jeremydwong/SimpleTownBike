import streamlit as st
from utils import run_async, format_device_name

def render_header():
    """Render the application header."""
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image('assets/bike_icon.svg', width=50)
    with col2:
        st.title("SimpleTownBike")
    st.markdown("---")

def render_device_scanner():
    """Render the device scanning section."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Bluetooth Device Scanner")
    
    with col2:
        if st.button("Scan Devices", disabled=st.session_state.scanning):
            st.session_state.scanning = True
            with st.spinner("Scanning for devices..."):
                st.session_state.devices = run_async(
                    lambda: st.session_state.ble_manager.scan_devices())
            st.session_state.scanning = False
            st.rerun()

def render_device_selector():
    """Render the device selection dropdown."""
    if st.session_state.devices:
        device_options = {format_device_name(d): d for d in st.session_state.devices}
        selected_device = st.selectbox(
            "Select a device to connect:",
            options=list(device_options.keys()),
            index=None
        )
        
        if selected_device:
            device = device_options[selected_device]
            if st.button("Connect"):
                with st.spinner("Connecting..."):
                    success = run_async(
                        lambda: st.session_state.ble_manager.connect_device(device['address']))
                    if success:
                        st.session_state.connected_device = device
                        st.success(f"Connected to {device['name']}")
                        st.rerun()
                    else:
                        st.error("Failed to connect to device")

def render_connected_device():
    """Render the connected device information."""
    if st.session_state.connected_device:
        st.subheader("Connected Device")
        st.write(f"Name: {st.session_state.connected_device['name']}")
        st.write(f"Address: {st.session_state.connected_device['address']}")
        
        if st.button("Disconnect"):
            with st.spinner("Disconnecting..."):
                success = run_async(
                    lambda: st.session_state.ble_manager.disconnect_device())
                if success:
                    st.session_state.connected_device = None
                    st.success("Device disconnected")
                    st.rerun()
                else:
                    st.error("Failed to disconnect device")
