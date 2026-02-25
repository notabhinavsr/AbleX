"""
AbleX — Gesture-Controlled Accessibility App
Double-click this file from the Desktop to launch.
"""

import sys
import os
import logging
from datetime import datetime

# ── Redirect output to log file ──────────────────────────
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "ablex.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)

class LogRedirect:
    """Redirect print() to both log file and nowhere (no console)."""
    def write(self, msg):
        if msg.strip():
            logging.info(msg.strip())
    def flush(self):
        pass

sys.stdout = LogRedirect()
sys.stderr = LogRedirect()

# ── Launch main app ──────────────────────────────────────
print(f"AbleX started at {datetime.now()}")

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Run the main module
import main
