import asyncio
from bleak import BleakScanner, BleakClient, BleakError
from typing import Optional, Callable, List, Dict
import logging
import platform
import os
import time
import numpy as np

logger = logging.getLogger(__name__)

# FTMS characteristic UUIDs
FTMS_SERVICE_UUID = "00001826-0000-1000-8000-00805f9b34fb"
INDOOR_BIKE_DATA_UUID = "00002ad2-0000-1000-8000-00805f9b34fb"
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

class BluetoothNotAvailableError(Exception):
    pass

class BLEManager:
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.connected_device = None
        self.event_loop = None
        self.is_test_mode = os.getenv('BLE_TEST_MODE', '').lower() == 'true'
        self.known_fitness_services = {
            FTMS_SERVICE_UUID: "Fitness Machine Service",
            HEART_RATE_SERVICE_UUID: "Heart Rate Service",
        }
        # Extended metrics storage
        self.metrics = {
            'heart_rate': {'values': [], 'timestamps': []},
            'power': {'values': [], 'timestamps': []},
            'avg_power': {'values': [], 'timestamps': []},
            'cadence': {'values': [], 'timestamps': []},
            'avg_cadence': {'values': [], 'timestamps': []},
            'speed': {'values': [], 'timestamps': []},
            'avg_speed': {'values': [], 'timestamps': []},
            'distance': {'values': [], 'timestamps': []},
            'resistance': {'values': [], 'timestamps': []}
        }
        self.last_update = time.time()
        self.mock_data_task = None

    def _generate_mock_data(self):
        """Generate mock data for testing."""
        current_time = time.time()
        t = current_time - self.last_update
        
        # Generate more realistic mock data with time-based variations
        hr = 120 + 20 * np.sin(t/60)  # Heart rate varying between 100-140
        power = 180 + 40 * np.sin(t/30)  # Power varying between 140-220W
        cadence = 75 + 10 * np.sin(t/45)  # Cadence varying between 65-85
        speed = 25 + 5 * np.sin(t/90)  # Speed varying between 20-30 km/h
        distance = (t * speed / 3.6)  # Distance in meters
        resistance = 8 + 2 * np.sin(t/120)  # Resistance level between 6-10
        
        return {
            'heart_rate': max(60, min(200, hr)),
            'power': max(0, min(400, power)),
            'avg_power': max(0, min(400, np.mean(self.metrics['power']['values'][-10:] if self.metrics['power']['values'] else [power]))),
            'cadence': max(0, min(120, cadence)),
            'avg_cadence': max(0, min(120, np.mean(self.metrics['cadence']['values'][-10:] if self.metrics['cadence']['values'] else [cadence]))),
            'speed': max(0, min(50, speed)),
            'avg_speed': max(0, min(50, np.mean(self.metrics['speed']['values'][-10:] if self.metrics['speed']['values'] else [speed]))),
            'distance': distance,
            'resistance': max(1, min(20, resistance))
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

    def _handle_heart_rate_data(self, sender: int, data: bytearray):
        """Handle heart rate measurement data."""
        try:
            heart_rate = data[1]
            current_time = time.time()
            self.metrics['heart_rate']['values'].append(heart_rate)
            self.metrics['heart_rate']['timestamps'].append(current_time)
            
            # Use the stored event loop for notifications
            if self.event_loop:
                self.event_loop.call_soon_threadsafe(lambda: None)
        except Exception as e:
            logger.error(f"Error processing heart rate data: {e}")

    def _handle_indoor_bike_data(self, sender: int, data: bytearray):
        """Handle indoor bike data according to FTMS specification."""
        try:
            current_time = time.time()
            flags = data[0]
            current_index = 2  # Start after flags and instantaneous speed

            # Parse data based on flags
            metrics_data = {}
            
            # More Data (Bit 0) - reserved for future use
            
            # Average Speed Present (Bit 1)
            if flags & (1 << 1):
                avg_speed = int.from_bytes(data[current_index:current_index+2], byteorder='little') / 100  # km/h
                metrics_data['avg_speed'] = avg_speed
                current_index += 2

            # Instantaneous Cadence Present (Bit 2)
            if flags & (1 << 2):
                cadence = int.from_bytes(data[current_index:current_index+2], byteorder='little') / 2  # rpm
                metrics_data['cadence'] = cadence
                current_index += 2

            # Average Cadence Present (Bit 3)
            if flags & (1 << 3):
                avg_cadence = int.from_bytes(data[current_index:current_index+2], byteorder='little') / 2  # rpm
                metrics_data['avg_cadence'] = avg_cadence
                current_index += 2

            # Total Distance Present (Bit 4)
            if flags & (1 << 4):
                distance = int.from_bytes(data[current_index:current_index+3], byteorder='little')  # meters
                metrics_data['distance'] = distance
                current_index += 3

            # Resistance Level Present (Bit 5)
            if flags & (1 << 5):
                resistance = int.from_bytes(data[current_index:current_index+2], byteorder='little')
                metrics_data['resistance'] = resistance
                current_index += 2

            # Instantaneous Power Present (Bit 6)
            if flags & (1 << 6):
                power = int.from_bytes(data[current_index:current_index+2], byteorder='little')  # watts
                metrics_data['power'] = power
                current_index += 2

            # Average Power Present (Bit 7)
            if flags & (1 << 7):
                avg_power = int.from_bytes(data[current_index:current_index+2], byteorder='little')  # watts
                metrics_data['avg_power'] = avg_power

            # Update metrics
            for metric, value in metrics_data.items():
                self.metrics[metric]['values'].append(value)
                self.metrics[metric]['timestamps'].append(current_time)

            # Use the stored event loop for notifications
            if self.event_loop:
                self.event_loop.call_soon_threadsafe(lambda: None)
                
        except Exception as e:
            logger.error(f"Error processing indoor bike data: {e}")

    async def connect_device(self, address: str, callback: Callable = None) -> bool:
        """Connect to a specific device."""
        if self.is_test_mode:
            self.connected_device = address
            # Create and store event loop reference for test mode
            self.event_loop = asyncio.get_event_loop()
            self.mock_data_task = asyncio.create_task(self._mock_data_loop())
            if callback:
                await callback()
            return True

        try:
            # Create and store event loop reference
            self.event_loop = asyncio.get_event_loop()
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected_device = address
            
            # Subscribe to notifications for each service
            services = await self.client.get_services()
            for service in services:
                if service.uuid == FTMS_SERVICE_UUID:
                    char = self.client.services.get_characteristic(INDOOR_BIKE_DATA_UUID)
                    if char:
                        await self.client.start_notify(char.uuid, self._handle_indoor_bike_data)
                elif service.uuid == HEART_RATE_SERVICE_UUID:
                    char = self.client.services.get_characteristic(HEART_RATE_MEASUREMENT_UUID)
                    if char:
                        await self.client.start_notify(char.uuid, self._handle_heart_rate_data)
            
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
        try:
            if self.is_test_mode:
                if self.mock_data_task:
                    self.mock_data_task.cancel()
                    self.mock_data_task = None
                self.connected_device = None
                self.event_loop = None
                return True

            if self.client and self.client.is_connected:
                # Cleanup notifications before disconnecting
                for service in self.client.services:
                    for char in service.characteristics:
                        await self.client.stop_notify(char.uuid)
                await self.client.disconnect()
            self.client = None
            self.connected_device = None
            self.event_loop = None
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if currently connected to a device."""
        if self.is_test_mode:
            return self.connected_device is not None
        return self.client is not None and self.client.is_connected

    def get_metrics_data(self) -> Dict:
        """Get the current metrics data."""
        return self.metrics

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
