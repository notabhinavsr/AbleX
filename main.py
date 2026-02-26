"""
main.py — Serial loop + click pattern logic
Runs in a background thread. Called by gui.py.
"""

import serial
import pyautogui
import time
import threading

import config
from stt_handler import trigger_stt, is_listening


# ── State for GUI ────────────────────────────────────────
connection_status = "disconnected"
_serial_thread = None
_running = False


def get_status():
    return connection_status


# ── CLICK PATTERN DETECTION ──────────────────────────────
# Simple timestamp-based approach — no threading timers.
# Each CLK increments click_count and records the time.
# The serial loop checks on every iteration if the window expired.
CLICK_WAIT = 1.0  # 1 second window — generous for limited mobility users

click_count = 0
last_click_time = 0


def handle_click():
    """Register a click event."""
    global click_count, last_click_time
    now = time.time()

    # If too long since last click, start fresh count
    if now - last_click_time > CLICK_WAIT:
        click_count = 0

    click_count += 1
    last_click_time = now
    print(f"[CLICK] Press #{click_count}...")

    # Triple-click: fire right-click immediately
    if click_count >= 3:
        print("[CLICK] Triple → Right click")
        pyautogui.click(button='right')
        click_count = 0
        last_click_time = 0


def check_pending_clicks():
    """Check if click window has expired and fire the action.
    Called every serial loop iteration."""
    global click_count, last_click_time

    if click_count == 0 or last_click_time == 0:
        return

    elapsed = time.time() - last_click_time
    if elapsed < CLICK_WAIT:
        return  # still waiting for more clicks

    # Window expired — fire based on count
    count = click_count
    click_count = 0
    last_click_time = 0

    if count == 1:
        print("[CLICK] Single → Left click")
        pyautogui.click(button='left')
    elif count == 2:
        print("[CLICK] Double → Double click")
        pyautogui.doubleClick(button='left')


# ── SERIAL LOOP (runs in thread) ─────────────────────────
def start_serial_loop():
    global _serial_thread, _running
    if _serial_thread and _serial_thread.is_alive():
        print("[WARN] Serial loop already running")
        return
    _running = True
    _serial_thread = threading.Thread(target=_serial_loop, daemon=True)
    _serial_thread.start()


def stop_serial_loop():
    global _running
    _running = False


def _serial_loop():
    global connection_status, _running

    try:
        print(f"[INFO] Opening {config.COM_PORT}...")
        ser = serial.Serial(config.COM_PORT, config.BAUD_RATE, timeout=0.1)

        ser.dtr = False
        ser.rts = False
        time.sleep(0.1)
        ser.dtr = True
        ser.rts = True
        time.sleep(2)

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        connection_status = "connected"
        print(f"[INFO] Connected to {config.COM_PORT}")
        print("[AbleX] Ready!\n")

    except serial.SerialException as e:
        connection_status = "error"
        print(f"[ERROR] Cannot open {config.COM_PORT}: {e}")
        return

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    while _running:
        try:
            raw = ser.readline()

            # Check pending clicks every iteration (even on empty reads)
            check_pending_clicks()

            if not raw or raw.strip() == b'':
                continue

            line = raw.decode(errors='ignore').strip()
            if not line:
                continue

            # ───── BUTTON 1 → CLICK ─────
            if line in ("CLK", "LC", "C,L"):
                handle_click()
                continue

            # ───── BUTTON 2 → STT ─────
            if line == "STT":
                if not is_listening():
                    print("[STT] ✦ Button 2 → Voice typing...")
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

                if abs(dx) < config.DEADZONE:
                    dx = 0
                if abs(dy) < config.DEADZONE:
                    dy = 0

                move_x = int(-dx * config.SENSITIVITY)
                move_y = int(-dy * config.SENSITIVITY)

                if move_x != 0 or move_y != 0:
                    pyautogui.moveRel(move_x, move_y, _pause=False)

        except serial.SerialException:
            connection_status = "error"
            print("[ERROR] Serial connection lost")
            break
        except Exception as e:
            print(f"[ERROR] {e}")

    connection_status = "disconnected"
    try:
        ser.close()
    except Exception:
        pass
    print("[INFO] Serial loop stopped")


# ── Allow running standalone for testing ─────────────────
if __name__ == "__main__":
    print("[AbleX] Starting standalone...")
    screen_w, screen_h = pyautogui.size()
    print(f"[INFO] Screen: {screen_w}x{screen_h}")
    print("[INFO] Controls:")
    print("       Button 1: x1=select, x2=open, x3=right-click")
    print("       Button 2: Voice typing (STT)")

    start_serial_loop()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_serial_loop()
        print("\n[AbleX] Stopped")