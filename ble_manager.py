import asyncio
from bleak import BleakScanner, BleakClient
from typing import Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

class BLEManager:
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.connected_device = None
        self.known_fitness_services = [
            "0x1826",  # Fitness Machine Service
            "0x180D",  # Heart Rate Service
            "0x1818",  # Cycling Power Service
        ]

    async def scan_devices(self) -> List[dict]:
        """Scan for BLE devices and return fitness-related ones."""
        try:
            devices = await BleakScanner.discover()
            fitness_devices = []
            
            for device in devices:
                # Filter for fitness devices (basic filtering)
                device_name = str(device.name).lower()
                if (device_name and any(keyword in device_name 
                    for keyword in ['bike', 'cycle', 'fitness', 'heart', 'polar', 'wahoo', 'garmin'])):
                    fitness_devices.append({
                        'name': device.name or 'Unknown Device',
                        'address': device.address,
                        'rssi': device.rssi
                    })
            
            return sorted(fitness_devices, key=lambda x: x['rssi'], reverse=True)
        except Exception as e:
            logger.error(f"Error scanning devices: {e}")
            raise

    async def connect_device(self, address: str, callback: Callable = None) -> bool:
        """Connect to a specific device."""
        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected_device = address
            
            if callback:
                await callback()
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            return False

    async def disconnect_device(self) -> bool:
        """Disconnect from the current device."""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                self.client = None
                self.connected_device = None
            return True
        except Exception as e:
            logger.error(f"Error disconnecting device: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if currently connected to a device."""
        return self.client is not None and self.client.is_connected
