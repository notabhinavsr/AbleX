"""
notification.py — Transparent STT overlay notification
Shows a floating pill banner at the top of the screen.
"""

import tkinter as tk
import threading


class NotificationOverlay:
    """Always-on-top transparent notification pill."""

    def __init__(self):
        self._root = None
        self._label = None
        self._visible = False
        self._hide_timer = None

    def _ensure_root(self):
        """Create the overlay window (must be called from main thread or own thread)."""
        if self._root is not None:
            return

        self._root = tk.Toplevel()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.9)
        self._root.configure(bg="#1a1a2e")

        # Position at top-center
        screen_w = self._root.winfo_screenwidth()
        w, h = 320, 50
        x = (screen_w - w) // 2
        y = 20
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._label = tk.Label(
            self._root,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="#00d4ff",
            bg="#1a1a2e",
            padx=20,
            pady=8,
        )
        self._label.pack(expand=True, fill="both")

        # Start hidden
        self._root.withdraw()

    def show(self, text, color="#00d4ff", auto_hide=0):
        """Show notification with text. auto_hide in seconds (0=manual)."""
        try:
            self._ensure_root()

            if self._hide_timer:
                self._root.after_cancel(self._hide_timer)
                self._hide_timer = None

            self._label.config(text=text, fg=color)
            self._root.deiconify()
            self._root.lift()
            self._visible = True

            if auto_hide > 0:
                self._hide_timer = self._root.after(
                    int(auto_hide * 1000), self.hide
                )
        except Exception:
            pass

    def hide(self):
        """Hide the notification."""
        try:
            if self._root:
                self._root.withdraw()
                self._visible = False
        except Exception:
            pass

    def on_stt_state(self, state):
        """Callback for stt_handler state changes."""
        if state == "listening":
            self.show("🎙️  Listening...", color="#00d4ff")
        elif state == "transcribing":
            self.show("☁️  Transcribing...", color="#ffaa00")
        elif state == "typing":
            self.show("⌨️  Typing...", color="#00ff88")
        elif state == "done":
            self.show("✅  Done", color="#00ff88", auto_hide=2)
        elif state == "error":
            self.show("❌  Error", color="#ff4444", auto_hide=3)
