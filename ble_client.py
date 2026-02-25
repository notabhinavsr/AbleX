import asyncio
from bleak import BleakClient

DEVICE_NAME = "HeadMouse"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef0"

class BLEClient:
    def __init__(self, callback):
        self.callback = callback

    async def connect(self, address):
        async with BleakClient(address) as client:
            await client.start_notify(CHAR_UUID, self.callback)
            print("Connected to device")
            while True:
                await asyncio.sleep(1)