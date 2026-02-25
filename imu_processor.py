import struct
from config import DEADZONE

def parse_imu(data: bytearray):
    dx, dy, _ = struct.unpack("<hhb", data[:5])

    if abs(dx) < DEADZONE:
        dx = 0
    if abs(dy) < DEADZONE:
        dy = 0

    return dx, dy