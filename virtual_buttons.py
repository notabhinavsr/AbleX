"""
virtual_buttons.py — Floating on-screen virtual buttons
Draggable, always-on-top, configurable actions.
"""

import json
import os
import tkinter as tk
import pyautogui
from stt_handler import trigger_stt, is_listening


BUTTONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "buttons.json")

# ── Button size and style ────────────────────────────────
BTN_SIZE = 52
BTN_FONT = ("Segoe UI", 16)
BTN_BG   = "#2a2a3e"
BTN_FG   = "#e0e0ff"
BTN_HOVER = "#3d3d5c"
BTN_BORDER = "#5555aa"


def load_buttons():
    """Load button configurations from JSON."""
    if os.path.exists(BUTTONS_FILE):
        try:
            with open(BUTTONS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_buttons(buttons_data):
    """Save button configs + positions to JSON."""
    with open(BUTTONS_FILE, "w") as f:
        json.dump(buttons_data, f, indent=2)


def execute_action(action, value):
    """Execute a virtual button action."""
    if action == "key":
        print(f"[VBTN] Key: {value}")
        pyautogui.press(value)
    elif action == "scroll":
        amount = int(value)
        print(f"[VBTN] Scroll: {amount}")
        pyautogui.scroll(amount)
    elif action == "stt":
        if not is_listening():
            print("[VBTN] Triggering STT")
            trigger_stt()
    elif action == "hotkey":
        keys = [k.strip() for k in value.split("+")]
        print(f"[VBTN] Hotkey: {'+'.join(keys)}")
        pyautogui.hotkey(*keys)
    elif action == "click":
        btn = value if value else "left"
        print(f"[VBTN] Click: {btn}")
        pyautogui.click(button=btn)
    elif action == "type":
        print(f"[VBTN] Type: {value}")
        pyautogui.write(value, interval=0.02)


class FloatingButton:
    """A single draggable floating button."""

    def __init__(self, parent_root, btn_data, index, on_move=None):
        self.data = btn_data
        self.index = index
        self.on_move = on_move

        self.win = tk.Toplevel(parent_root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.85)
        self.win.configure(bg=BTN_BORDER)

        x = btn_data.get("x", 50)
        y = btn_data.get("y", 100 + index * 70)
        self.win.geometry(f"{BTN_SIZE}x{BTN_SIZE}+{x}+{y}")

        self.btn = tk.Label(
            self.win,
            text=btn_data.get("label", "?"),
            font=BTN_FONT,
            bg=BTN_BG,
            fg=BTN_FG,
            cursor="hand2",
            relief="flat",
            bd=0,
        )
        self.btn.pack(expand=True, fill="both", padx=1, pady=1)

        # Tooltip on hover
        tooltip = btn_data.get("tooltip", "")
        if tooltip:
            self._create_tooltip(tooltip)

        # Click → execute action
        self.btn.bind("<Button-1>", self._on_click)

        # Drag support
        self._drag_data = {"x": 0, "y": 0, "dragging": False}
        self.btn.bind("<ButtonPress-3>", self._drag_start)     # right-click drag
        self.btn.bind("<B3-Motion>", self._drag_motion)
        self.btn.bind("<ButtonRelease-3>", self._drag_end)

        # Hover effects
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=BTN_HOVER))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=BTN_BG))

    def _on_click(self, event):
        action = self.data.get("action", "")
        value = self.data.get("value", "")
        execute_action(action, value)

    def _drag_start(self, event):
        self._drag_data["x"] = event.x_root - self.win.winfo_x()
        self._drag_data["y"] = event.y_root - self.win.winfo_y()
        self._drag_data["dragging"] = True

    def _drag_motion(self, event):
        if self._drag_data["dragging"]:
            x = event.x_root - self._drag_data["x"]
            y = event.y_root - self._drag_data["y"]
            self.win.geometry(f"+{x}+{y}")

    def _drag_end(self, event):
        self._drag_data["dragging"] = False
        self.data["x"] = self.win.winfo_x()
        self.data["y"] = self.win.winfo_y()
        if self.on_move:
            self.on_move()

    def _create_tooltip(self, text):
        tip = None
        def show(e):
            nonlocal tip
            tip = tk.Toplevel(self.win)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            x = self.win.winfo_x() + BTN_SIZE + 5
            y = self.win.winfo_y()
            tip.geometry(f"+{x}+{y}")
            lbl = tk.Label(tip, text=text, font=("Segoe UI", 10),
                           bg="#1a1a2e", fg="#aaaacc", padx=8, pady=4)
            lbl.pack()
        def hide(e):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None
        self.btn.bind("<Enter>", lambda e: (self.btn.config(bg=BTN_HOVER), show(e)))
        self.btn.bind("<Leave>", lambda e: (self.btn.config(bg=BTN_BG), hide(e)))

    def destroy(self):
        self.win.destroy()


class VirtualButtonManager:
    """Manages all floating virtual buttons."""

    def __init__(self, parent_root):
        self.parent = parent_root
        self.buttons_data = load_buttons()
        self.floating_buttons = []
        self._create_buttons()

    def _create_buttons(self):
        for i, data in enumerate(self.buttons_data):
            fb = FloatingButton(self.parent, data, i, on_move=self._save)
            self.floating_buttons.append(fb)

    def _save(self):
        save_buttons(self.buttons_data)

    def add_button(self, label, tooltip, action, value):
        """Add a new virtual button."""
        data = {
            "label": label,
            "tooltip": tooltip,
            "action": action,
            "value": value,
            "x": 50,
            "y": 100 + len(self.buttons_data) * 70,
        }
        self.buttons_data.append(data)
        fb = FloatingButton(self.parent, data, len(self.floating_buttons), on_move=self._save)
        self.floating_buttons.append(fb)
        self._save()

    def remove_button(self, index):
        """Remove a virtual button by index."""
        if 0 <= index < len(self.floating_buttons):
            self.floating_buttons[index].destroy()
            self.floating_buttons.pop(index)
            self.buttons_data.pop(index)
            self._save()

    def show_all(self):
        for fb in self.floating_buttons:
            fb.win.deiconify()

    def hide_all(self):
        for fb in self.floating_buttons:
            fb.win.withdraw()

    def destroy_all(self):
        for fb in self.floating_buttons:
            fb.destroy()
        self.floating_buttons.clear()

    def get_data(self):
        return self.buttons_data
