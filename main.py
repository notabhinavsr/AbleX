import serial
import pyautogui
import time

# ── CONFIG ───────────────────────────────────────────────
COM_PORT    = "COM8"
BAUD_RATE   = 115200
SENSITIVITY = 1
DEADZONE    = 2

# ── SETUP ────────────────────────────────────────────────
print(f"[INFO] Opening {COM_PORT}...")
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

# Toggle DTR/RTS to reset ESP32 (forces reboot so it starts sending)
ser.dtr = False
ser.rts = False
time.sleep(0.1)
ser.dtr = True
ser.rts = True
time.sleep(2)

ser.reset_input_buffer()
ser.reset_output_buffer()

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

screen_w, screen_h = pyautogui.size()
print(f"[INFO] Connected to {COM_PORT}")
print(f"[INFO] Screen: {screen_w}x{screen_h}")
print("[INFO] Waiting for ESP32 data...\n")

# ── MAIN LOOP ────────────────────────────────────────────
empty_count = 0
while True:
    try:
        raw = ser.readline()

        if not raw or raw.strip() == b'':
            empty_count += 1
            if empty_count % 20 == 0:
                print(f"[WAIT] No data... ({empty_count} timeouts)")
                # Show how many bytes are waiting in the buffer
                print(f"       Bytes in buffer: {ser.in_waiting}")
            continue

        # Got data — print it raw for debugging
        empty_count = 0
        line = raw.decode(errors='ignore').strip()
        if not line:
            continue

        # ───── CLICK COMMANDS ─────
        if line in ("LC", "C,L"):
            print("[CLICK] LEFT")
            pyautogui.click(button='left')
            continue

        if line in ("RC", "C,R"):
            print("[CLICK] RIGHT")
            pyautogui.click(button='right')
            continue

        # ───── CURSOR MOVEMENT ─────
        # Supports both "dx,dy" and "M,dx,dy" formats
        if "," in line:
            parts = line.split(",")

            dx_str, dy_str = None, None

            if len(parts) == 2:
                dx_str, dy_str = parts[0], parts[1]
            elif len(parts) == 3 and parts[0] == "M":
                dx_str, dy_str = parts[1], parts[2]
            else:
                print(f"[DATA] {line}")
                continue

            try:
                dx = float(dx_str)
                dy = float(dy_str)
            except ValueError:
                print(f"[WARN] Bad data: {line}")
                continue

            # Deadzone
            if abs(dx) < DEADZONE:
                dx = 0
            if abs(dy) < DEADZONE:
                dy = 0

            move_x = int(-dx * SENSITIVITY)
            move_y = int(-dy * SENSITIVITY)

            if move_x != 0 or move_y != 0:
                print(f"[MOVE] ({move_x}, {move_y})")
                pyautogui.moveRel(move_x, move_y, _pause=False)

        else:
            print(f"[DATA] {line}")


    except KeyboardInterrupt:
        print("\n[INFO] Stopped")
        break

    except Exception as e:
        print(f"[ERROR] {e}")