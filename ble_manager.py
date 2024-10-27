import asyncio
from bleak import BleakScanner, BleakClient, BleakError
from typing import Optional, Callable, List, Dict
import logging
import platform
import os
import time
import numpy as np

logger = logging.getLogger(__name__)

class BluetoothNotAvailableError(Exception):
    pass

class BLEManager:
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.connected_device = None
        self.is_test_mode = os.getenv('BLE_TEST_MODE', '').lower() == 'true'
        self.known_fitness_services = {
            "0x1826": "Fitness Machine Service",
            "0x180D": "Heart Rate Service",
            "0x1818": "Cycling Power Service",
        }
        # Data storage for metrics
        self.metrics = {
            'heart_rate': {'values': [], 'timestamps': []},
            'power': {'values': [], 'timestamps': []},
            'cadence': {'values': [], 'timestamps': []}
        }
        self.last_update = time.time()
        self.mock_data_task = None

    def _generate_mock_data(self):
        """Generate mock data for testing."""
        hr = np.random.normal(140, 10)  # Heart rate around 140 bpm
        power = np.random.normal(200, 20)  # Power around 200W
        cadence = np.random.normal(80, 5)  # Cadence around 80 rpm
        
        return {
            'heart_rate': max(60, min(200, hr)),
            'power': max(0, min(400, power)),
            'cadence': max(0, min(120, cadence))
        }

    async def _mock_data_loop(self):
        """Generate mock data periodically in test mode."""
        while self.is_connected():
            mock_data = self._generate_mock_data()
            current_time = time.time()
            
            for metric, value in mock_data.items():
                self.metrics[metric]['values'].append(value)
                self.metrics[metric]['timestamps'].append(current_time)
                
                # Keep only last 5 minutes of data
                cutoff = current_time - 300
                while (self.metrics[metric]['timestamps'] and 
                       self.metrics[metric]['timestamps'][0] < cutoff):
                    self.metrics[metric]['values'].pop(0)
                    self.metrics[metric]['timestamps'].pop(0)
            
            await asyncio.sleep(1)

    async def check_bluetooth_availability(self):
        """Check if Bluetooth is available on the system."""
        try:
            if platform.system() == "Linux":
                import dbus
                bus = dbus.SystemBus()
                adapter = bus.get_object('org.bluez', '/org/bluez/hci0')
                return True
            elif platform.system() == "Windows":
                import ctypes
                return ctypes.windll.bthprops.BluetoothIsDiscoverable(None) >= 0
            elif platform.system() == "Darwin":
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

    def _handle_heart_rate_data(self, sender: int, data: bytearray):
        """Handle heart rate measurement data."""
        try:
            heart_rate = data[1]
            current_time = time.time()
            self.metrics['heart_rate']['values'].append(heart_rate)
            self.metrics['heart_rate']['timestamps'].append(current_time)
        except Exception as e:
            logger.error(f"Error processing heart rate data: {e}")

    def _handle_power_data(self, sender: int, data: bytearray):
        """Handle cycling power measurement data."""
        try:
            power = int.from_bytes(data[2:4], byteorder='little')
            current_time = time.time()
            self.metrics['power']['values'].append(power)
            self.metrics['power']['timestamps'].append(current_time)
        except Exception as e:
            logger.error(f"Error processing power data: {e}")

    def _handle_cadence_data(self, sender: int, data: bytearray):
        """Handle cadence measurement data."""
        try:
            cadence = int.from_bytes(data[4:6], byteorder='little')
            current_time = time.time()
            self.metrics['cadence']['values'].append(cadence)
            self.metrics['cadence']['timestamps'].append(current_time)
        except Exception as e:
            logger.error(f"Error processing cadence data: {e}")

    async def connect_device(self, address: str, callback: Callable = None) -> bool:
        """Connect to a specific device."""
        if self.is_test_mode:
            self.connected_device = address
            # Start mock data generation
            self.mock_data_task = asyncio.create_task(self._mock_data_loop())
            if callback:
                await callback()
            return True

        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected_device = address
            
            # Subscribe to notifications for each service
            services = await self.client.get_services()
            for service in services:
                if "heart rate" in service.description.lower():
                    for char in service.characteristics:
                        if "measurement" in char.description.lower():
                            await self.client.start_notify(char.uuid, self._handle_heart_rate_data)
                elif "cycling power" in service.description.lower():
                    for char in service.characteristics:
                        if "measurement" in char.description.lower():
                            await self.client.start_notify(char.uuid, self._handle_power_data)
                            await self.client.start_notify(char.uuid, self._handle_cadence_data)
            
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
            if self.mock_data_task:
                self.mock_data_task.cancel()
                self.mock_data_task = None
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

    def get_metrics_data(self) -> Dict:
        """Get the current metrics data."""
        return self.metrics
