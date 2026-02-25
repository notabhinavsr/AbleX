import serial
import pyautogui
import time
import threading

from config import COM_PORT, BAUD_RATE, SENSITIVITY, DEADZONE
from stt_handler import trigger_stt, is_listening

# ── SETUP ────────────────────────────────────────────────
print("[AbleX] Starting...")
print(f"[INFO] Opening {COM_PORT}...")
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

# Toggle DTR/RTS to reset ESP32
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
print("[INFO] Controls:")
print("       Short press x1 = Left click (select)")
print("       Short press x2 = Double click (open)")
print("       Short press x3 = Right click")
print("       Long  press    = Voice typing (STT)")
print("[AbleX] Ready!\n")

# ── CLICK PATTERN DETECTION ──────────────────────────────
CLICK_WAIT = 0.5  # seconds to wait after last CLK before deciding

click_count = 0
click_timer = None
click_lock = threading.Lock()


def _execute_click_action():
    """Called after CLICK_WAIT — executes action based on click count."""
    global click_count
    with click_lock:
        count = click_count
        click_count = 0

    if count == 1:
        print("[CLICK] Single → Left click (select)")
        pyautogui.click(button='left')
    elif count == 2:
        print("[CLICK] Double → Double click (open)")
        pyautogui.doubleClick(button='left')
    elif count >= 3:
        print("[CLICK] Triple → Right click")
        pyautogui.click(button='right')


def handle_click():
    """Register a CLK event and schedule action after CLICK_WAIT."""
    global click_count, click_timer
    with click_lock:
        click_count += 1
        current = click_count

    # Cancel previous timer
    if click_timer is not None:
        click_timer.cancel()

    # Triple-click: fire immediately
    if current >= 3:
        _execute_click_action()
    else:
        # Wait to see if more clicks come
        click_timer = threading.Timer(CLICK_WAIT, _execute_click_action)
        click_timer.daemon = True
        click_timer.start()


# ── MAIN LOOP ────────────────────────────────────────────
empty_count = 0
while True:
    try:
        raw = ser.readline()

        if not raw or raw.strip() == b'':
            empty_count += 1
            if empty_count % 50 == 0:
                print(f"[WAIT] No data... ({empty_count} timeouts)")
            continue

        empty_count = 0
        line = raw.decode(errors='ignore').strip()
        if not line:
            continue

        # ───── BUTTON PRESS (short press) ─────
        if line in ("CLK", "LC", "C,L"):
            handle_click()
            continue

        # ───── RIGHT CLICK (long press) ─────
        if line in ("RC", "C,R"):
            if not is_listening():
                print("[STT] ✦ Long press → Starting voice typing...")
                trigger_stt()
            else:
                print("[STT] Already listening...")
            continue

        # ───── CURSOR MOVEMENT ─────
        if "," in line:
            parts = line.split(",")

            dx_str, dy_str = None, None

            if len(parts) == 2:
                dx_str, dy_str = parts[0], parts[1]
            elif len(parts) == 3 and parts[0] == "M":
                dx_str, dy_str = parts[1], parts[2]
            else:
                continue

            try:
                dx = float(dx_str)
                dy = float(dy_str)
            except ValueError:
                continue

            # Deadzone
            if abs(dx) < DEADZONE:
                dx = 0
            if abs(dy) < DEADZONE:
                dy = 0

            move_x = int(-dx * SENSITIVITY)
            move_y = int(-dy * SENSITIVITY)

            if move_x != 0 or move_y != 0:
                pyautogui.moveRel(move_x, move_y, _pause=False)

    except KeyboardInterrupt:
        print("\n[AbleX] Stopped")
        break

    except Exception as e:
        print(f"[ERROR] {e}")