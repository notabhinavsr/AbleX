import json
import os

# ── Serial ────────────────────────────────────────────────
COM_PORT   = "COM8"
BAUD_RATE  = 115200

# ── Cursor ────────────────────────────────────────────────
SENSITIVITY = 1
DEADZONE    = 2

# ── Sarvam AI STT ─────────────────────────────────────────
SARVAM_API_KEY = "sk_hzd0v1qi_yt8AgefoNsE21mqzlXODnz82"
SARVAM_MODEL   = "saaras:v3"
SARVAM_MODE    = "transcribe"

# ── Voice Typing ──────────────────────────────────────────
SILENCE_TIMEOUT     = 6
SILENCE_THRESHOLD   = 300
TRIPLE_CLICK_WINDOW = 1.5
SAMPLE_RATE         = 16000

# ── Settings persistence ─────────────────────────────────
_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def save_settings():
    """Save current settings to JSON."""
    data = {
        "COM_PORT": COM_PORT,
        "SENSITIVITY": SENSITIVITY,
        "DEADZONE": DEADZONE,
        "SILENCE_TIMEOUT": SILENCE_TIMEOUT,
    }
    with open(_SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_settings():
    """Load settings from JSON if exists."""
    global COM_PORT, SENSITIVITY, DEADZONE, SILENCE_TIMEOUT
    if os.path.exists(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE) as f:
                data = json.load(f)
            COM_PORT = data.get("COM_PORT", COM_PORT)
            SENSITIVITY = data.get("SENSITIVITY", SENSITIVITY)
            DEADZONE = data.get("DEADZONE", DEADZONE)
            SILENCE_TIMEOUT = data.get("SILENCE_TIMEOUT", SILENCE_TIMEOUT)
        except Exception:
            pass

# Auto-load on import
load_settings()