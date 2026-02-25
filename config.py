
# ── Serial ────────────────────────────────────────────────
COM_PORT   = "COM8"
BAUD_RATE  = 115200

# ── Cursor ────────────────────────────────────────────────
SENSITIVITY = 1
DEADZONE    = 2

# ── Sarvam AI STT ─────────────────────────────────────────
SARVAM_API_KEY = "sk_hzd0v1qi_yt8AgefoNsE21mqzlXODnz82"
SARVAM_MODEL   = "saaras:v3"
SARVAM_MODE    = "transcribe"   # transcribe | translate

# ── Voice Typing ──────────────────────────────────────────
SILENCE_TIMEOUT     = 6       # seconds of silence before auto-stop
SILENCE_THRESHOLD   = 300     # RMS below this = silence
TRIPLE_CLICK_WINDOW = 1.5     # seconds window to detect triple-click
SAMPLE_RATE         = 16000   # 16 kHz for Sarvam API