import asyncio
from bleak import BleakScanner, BleakClient, BleakError
from typing import Optional, Callable, List
import logging
import platform
import os

logger = logging.getLogger(__name__)

class BluetoothNotAvailableError(Exception):
    pass

class BLEManager:
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.connected_device = None
        self.is_test_mode = os.getenv('BLE_TEST_MODE', '').lower() == 'true'
        self.known_fitness_services = [
            "0x1826",  # Fitness Machine Service
            "0x180D",  # Heart Rate Service
            "0x1818",  # Cycling Power Service
        ]

    async def check_bluetooth_availability(self):
        """Check if Bluetooth is available on the system."""
        try:
            if platform.system() == "Linux":
                # Check if D-Bus service is available
                import dbus
                bus = dbus.SystemBus()
                adapter = bus.get_object('org.bluez', '/org/bluez/hci0')
                return True
            elif platform.system() == "Windows":
                # Basic Windows bluetooth check
                import ctypes
                return ctypes.windll.bthprops.BluetoothIsDiscoverable(None) >= 0
            elif platform.system() == "Darwin":
                # Basic macOS bluetooth check
                import objc
                return True
        except Exception as e:
            logger.warning(f"Bluetooth check failed: {e}")
            return False

    def get_mock_devices(self) -> List[dict]:
        """Return mock devices for testing."""
        return [
            {'name': 'Mock Heart Rate Monitor', 'address': '00:11:22:33:44:55', 'rssi': -65},
            {'name': 'Mock Smart Bike', 'address': '66:77:88:99:AA:BB', 'rssi': -70},
        ]

    async def scan_devices(self) -> List[dict]:
        """Scan for BLE devices and return fitness-related ones."""
        if self.is_test_mode:
            return self.get_mock_devices()

        try:
            # Check Bluetooth availability first
            if not await self.check_bluetooth_availability():
                raise BluetoothNotAvailableError(
                    "Bluetooth is not available on this system. "
                    "Please check if your device has Bluetooth capability "
                    "and if it's turned on."
                )

            devices = await BleakScanner.discover()
            fitness_devices = []
            
            for device in devices:
                device_name = str(device.name).lower()
                if (device_name and any(keyword in device_name 
                    for keyword in ['bike', 'cycle', 'fitness', 'heart', 'polar', 'wahoo', 'garmin'])):
                    fitness_devices.append({
                        'name': device.name or 'Unknown Device',
                        'address': device.address,
                        'rssi': device.rssi
                    })
            
            return sorted(fitness_devices, key=lambda x: x['rssi'], reverse=True)

        except BluetoothNotAvailableError as e:
            logger.error(str(e))
            raise
        except BleakError as e:
            logger.error(f"Bluetooth error: {e}")
            raise BluetoothNotAvailableError(
                f"Failed to scan for devices: {str(e)}. "
                "Please check your Bluetooth connection."
            )
        except Exception as e:
            logger.error(f"Unexpected error during device scan: {e}")
            raise BluetoothNotAvailableError(
                "An unexpected error occurred while scanning for devices. "
                f"Error: {str(e)}"
            )

    async def connect_device(self, address: str, callback: Callable = None) -> bool:
        """Connect to a specific device."""
        if self.is_test_mode:
            self.connected_device = address
            if callback:
                await callback()
            return True

        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected_device = address
            
            if callback:
                await callback()
            
            return True
        except BleakError as e:
            logger.error(f"Failed to connect to device: {e}")
            raise BluetoothNotAvailableError(
                f"Failed to connect to device: {str(e)}. "
                "Please make sure the device is in range and powered on."
            )
        except Exception as e:
            logger.error(f"Unexpected error during device connection: {e}")
            return False

    async def disconnect_device(self) -> bool:
        """Disconnect from the current device."""
        if self.is_test_mode:
            self.connected_device = None
            return True

        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                self.client = None
                self.connected_device = None
            return True
        except BleakError as e:
            logger.error(f"Error disconnecting device: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during device disconnection: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if currently connected to a device."""
        if self.is_test_mode:
            return self.connected_device is not None
        return self.client is not None and self.client.is_connected
