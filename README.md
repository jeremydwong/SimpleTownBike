# SimpleTownBike

A Streamlit-based bike fitness tracking app with BLE device connectivity. This application allows you to connect to various fitness devices via Bluetooth Low Energy (BLE) and track your workout metrics.

## Features

- BLE device scanning and connection
- Support for fitness devices (heart rate monitors, smart bikes, etc.)
- Test mode for development without Bluetooth hardware
- Graceful error handling for Bluetooth-related issues

## Requirements

- Python 3.11 or higher
- Streamlit
- Bleak (for BLE connectivity)
- A device with Bluetooth capability (for production use)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SimpleTownBike.git
cd SimpleTownBike
```

2. Install dependencies:
```bash
pip install streamlit bleak
```

## Running the Application

1. For development with mock devices:
```bash
export BLE_TEST_MODE=true
streamlit run main.py
```

2. For production with real Bluetooth devices:
```bash
export BLE_TEST_MODE=false
streamlit run main.py
```

The application will be available at `http://localhost:8501`

## Environment Variables

- `BLE_TEST_MODE`: Set to 'true' to use mock devices for testing (default: false)

## Troubleshooting

### Common Issues

1. **Bluetooth Not Available**
   - Check if your device has Bluetooth capability
   - Ensure Bluetooth is turned on
   - Verify you have the necessary permissions
   - Try running in test mode with `BLE_TEST_MODE=true`

2. **Permission Issues on Linux**
   - Ensure your user has access to Bluetooth:
     ```bash
     sudo usermod -a -G bluetooth $USER
     ```
   - You may need to restart your system after this change

3. **Device Not Found**
   - Make sure the device is powered on and in range
   - Check if the device is in pairing mode
   - Try rescanning for devices

4. **Connection Failed**
   - Ensure the device isn't connected to another application
   - Try turning Bluetooth off and on again
   - Restart the application

### Development Tips

1. Use test mode during development:
```bash
export BLE_TEST_MODE=true
```

2. Check the application logs for detailed error messages

3. For debugging Bluetooth issues:
```bash
# Linux
sudo systemctl status bluetooth

# macOS
system_profiler SPBluetoothDataType

# Windows
Get-PnpDevice -Class Bluetooth
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
