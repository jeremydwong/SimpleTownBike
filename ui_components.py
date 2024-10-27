import streamlit as st
from utils import run_async, format_device_name
from ble_manager import BluetoothNotAvailableError

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
                try:
                    st.session_state.devices = run_async(
                        lambda: st.session_state.ble_manager.scan_devices())
                except BluetoothNotAvailableError as e:
                    st.error(str(e))
                    st.info("""
                    💡 Tip: If you're running this locally, make sure:
                    - Your device has Bluetooth capability
                    - Bluetooth is turned on
                    - You have the necessary permissions
                    
                    For development purposes, you can set BLE_TEST_MODE=true to use mock devices.
                    """)
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
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
                    try:
                        success = run_async(
                            lambda: st.session_state.ble_manager.connect_device(device['address']))
                        if success:
                            st.session_state.connected_device = device
                            st.success(f"Connected to {device['name']}")
                            st.rerun()
                    except BluetoothNotAvailableError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Failed to connect to device: {str(e)}")

def render_connected_device():
    """Render the connected device information."""
    if st.session_state.connected_device:
        st.subheader("Connected Device")
        st.write(f"Name: {st.session_state.connected_device['name']}")
        st.write(f"Address: {st.session_state.connected_device['address']}")
        
        if st.button("Disconnect"):
            with st.spinner("Disconnecting..."):
                try:
                    success = run_async(
                        lambda: st.session_state.ble_manager.disconnect_device())
                    if success:
                        st.session_state.connected_device = None
                        st.success("Device disconnected")
                        st.rerun()
                    else:
                        st.error("Failed to disconnect device")
                except Exception as e:
                    st.error(f"Error disconnecting device: {str(e)}")

def render_environment_info():
    """Render environment information."""
    st.sidebar.markdown("### Environment Info")
    is_test_mode = st.session_state.ble_manager.is_test_mode
    st.sidebar.info(f"{'🔧 Test Mode' if is_test_mode else '🔵 Production Mode'}")
    
    if is_test_mode:
        st.sidebar.warning("""
        Running in test mode with mock devices.
        Set BLE_TEST_MODE=false for real device scanning.
        """)
