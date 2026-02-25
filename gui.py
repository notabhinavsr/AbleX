"""
gui.py — AbleX Dashboard
Dark-themed control panel with status, settings, and virtual button manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading

# Add project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from main import start_serial_loop, stop_serial_loop, get_status
from stt_handler import add_state_callback, trigger_stt, is_listening
from notification import NotificationOverlay
from virtual_buttons import VirtualButtonManager, load_buttons, save_buttons


# ── Color Palette ────────────────────────────────────────
BG       = "#0f0f1a"
BG2      = "#1a1a2e"
BG3      = "#2a2a3e"
FG       = "#e0e0ff"
FG_DIM   = "#8888aa"
ACCENT   = "#00d4ff"
GREEN    = "#00ff88"
RED      = "#ff4455"
ORANGE   = "#ffaa00"


class AbleXApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AbleX — Gesture Controller")
        self.root.geometry("420x620")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Set icon-less dark title bar feel
        self.root.option_add("*Font", "Segoe\\ UI 10")

        # ── Notification overlay ─────────────────────────
        self.notification = NotificationOverlay()
        add_state_callback(self._on_stt_state_safe)

        # ── Virtual buttons ──────────────────────────────
        self.vbtn_manager = VirtualButtonManager(self.root)

        # ── Build UI ─────────────────────────────────────
        self._build_header()
        self._build_status()
        self._build_settings()
        self._build_vbtn_panel()
        self._build_footer()

        # ── Start serial ─────────────────────────────────
        self.root.after(500, self._start_serial)

        # ── Status updater ───────────────────────────────
        self._update_status()

        # ── Window close ─────────────────────────────────
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── HEADER ───────────────────────────────────────────
    def _build_header(self):
        frame = tk.Frame(self.root, bg=BG, pady=15)
        frame.pack(fill="x")

        tk.Label(
            frame, text="AbleX", font=("Segoe UI", 24, "bold"),
            fg=ACCENT, bg=BG
        ).pack()
        tk.Label(
            frame, text="Gesture-Controlled Accessibility",
            font=("Segoe UI", 10), fg=FG_DIM, bg=BG
        ).pack()

    # ── STATUS ───────────────────────────────────────────
    def _build_status(self):
        frame = tk.Frame(self.root, bg=BG2, padx=20, pady=12)
        frame.pack(fill="x", padx=15, pady=(0, 10))

        row = tk.Frame(frame, bg=BG2)
        row.pack(fill="x")

        tk.Label(row, text="ESP32", font=("Segoe UI", 11, "bold"),
                 fg=FG, bg=BG2).pack(side="left")

        self.status_dot = tk.Label(row, text="●", font=("Segoe UI", 14),
                                    fg=RED, bg=BG2)
        self.status_dot.pack(side="left", padx=(8, 4))

        self.status_label = tk.Label(row, text="Disconnected",
                                      font=("Segoe UI", 10), fg=FG_DIM, bg=BG2)
        self.status_label.pack(side="left")

        # STT status
        self.stt_label = tk.Label(frame, text="",
                                   font=("Segoe UI", 10), fg=ORANGE, bg=BG2)
        self.stt_label.pack(anchor="w", pady=(6, 0))

    # ── SETTINGS ─────────────────────────────────────────
    def _build_settings(self):
        frame = tk.LabelFrame(
            self.root, text="  Settings  ", font=("Segoe UI", 11, "bold"),
            fg=ACCENT, bg=BG2, bd=1, relief="groove",
            padx=15, pady=10
        )
        frame.pack(fill="x", padx=15, pady=(0, 10))

        # COM Port
        row = tk.Frame(frame, bg=BG2)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="COM Port:", fg=FG, bg=BG2,
                 font=("Segoe UI", 10)).pack(side="left")
        self.com_var = tk.StringVar(value=config.COM_PORT)
        com_entry = tk.Entry(row, textvariable=self.com_var, width=8,
                             bg=BG3, fg=FG, insertbackground=FG,
                             font=("Segoe UI", 10), relief="flat", bd=0)
        com_entry.pack(side="right")

        # Sensitivity
        row2 = tk.Frame(frame, bg=BG2)
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Sensitivity:", fg=FG, bg=BG2,
                 font=("Segoe UI", 10)).pack(side="left")
        self.sens_var = tk.IntVar(value=config.SENSITIVITY)
        self.sens_label = tk.Label(row2, text=str(config.SENSITIVITY),
                                    fg=ACCENT, bg=BG2, font=("Segoe UI", 10, "bold"),
                                    width=3)
        self.sens_label.pack(side="right")
        sens_scale = tk.Scale(
            row2, from_=1, to=10, orient="horizontal",
            variable=self.sens_var, bg=BG2, fg=FG, troughcolor=BG3,
            highlightthickness=0, bd=0, length=150, showvalue=False,
            command=lambda v: self._update_sens(v)
        )
        sens_scale.pack(side="right", padx=(0, 5))

        # Deadzone
        row3 = tk.Frame(frame, bg=BG2)
        row3.pack(fill="x", pady=3)
        tk.Label(row3, text="Deadzone:", fg=FG, bg=BG2,
                 font=("Segoe UI", 10)).pack(side="left")
        self.dz_var = tk.IntVar(value=config.DEADZONE)
        self.dz_label = tk.Label(row3, text=str(config.DEADZONE),
                                  fg=ACCENT, bg=BG2, font=("Segoe UI", 10, "bold"),
                                  width=3)
        self.dz_label.pack(side="right")
        dz_scale = tk.Scale(
            row3, from_=0, to=10, orient="horizontal",
            variable=self.dz_var, bg=BG2, fg=FG, troughcolor=BG3,
            highlightthickness=0, bd=0, length=150, showvalue=False,
            command=lambda v: self._update_dz(v)
        )
        dz_scale.pack(side="right", padx=(0, 5))

    def _update_sens(self, val):
        config.SENSITIVITY = int(val)
        self.sens_label.config(text=val)
        config.save_settings()

    def _update_dz(self, val):
        config.DEADZONE = int(val)
        self.dz_label.config(text=val)
        config.save_settings()

    # ── VIRTUAL BUTTON PANEL ─────────────────────────────
    def _build_vbtn_panel(self):
        frame = tk.LabelFrame(
            self.root, text="  Virtual Buttons  ", font=("Segoe UI", 11, "bold"),
            fg=ACCENT, bg=BG2, bd=1, relief="groove",
            padx=15, pady=10
        )
        frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Button list
        self.vbtn_listbox = tk.Listbox(
            frame, bg=BG3, fg=FG, font=("Segoe UI", 10),
            selectbackground=ACCENT, selectforeground=BG,
            relief="flat", bd=0, height=5
        )
        self.vbtn_listbox.pack(fill="both", expand=True, pady=(0, 8))
        self._refresh_vbtn_list()

        # Add / Remove buttons
        btn_row = tk.Frame(frame, bg=BG2)
        btn_row.pack(fill="x")

        add_btn = tk.Button(
            btn_row, text="+ Add Button", font=("Segoe UI", 9, "bold"),
            bg=ACCENT, fg=BG, relief="flat", bd=0, padx=12, pady=4,
            command=self._add_vbtn_dialog,
            activebackground="#33ddff", activeforeground=BG,
            cursor="hand2"
        )
        add_btn.pack(side="left")

        remove_btn = tk.Button(
            btn_row, text="Remove", font=("Segoe UI", 9),
            bg=RED, fg="white", relief="flat", bd=0, padx=12, pady=4,
            command=self._remove_vbtn,
            activebackground="#ff6677", activeforeground="white",
            cursor="hand2"
        )
        remove_btn.pack(side="right")

        toggle_btn = tk.Button(
            btn_row, text="Show/Hide", font=("Segoe UI", 9),
            bg=BG3, fg=FG, relief="flat", bd=0, padx=12, pady=4,
            command=self._toggle_vbtns,
            cursor="hand2"
        )
        toggle_btn.pack(side="right", padx=(0, 5))

    def _refresh_vbtn_list(self):
        self.vbtn_listbox.delete(0, "end")
        for btn in self.vbtn_manager.get_data():
            label = btn.get("label", "?")
            tooltip = btn.get("tooltip", "")
            action = btn.get("action", "")
            value = btn.get("value", "")
            self.vbtn_listbox.insert("end", f"  {label}  {tooltip}  →  {action}: {value}")

    _vbtns_visible = True

    def _toggle_vbtns(self):
        if self._vbtns_visible:
            self.vbtn_manager.hide_all()
        else:
            self.vbtn_manager.show_all()
        self._vbtns_visible = not self._vbtns_visible

    def _remove_vbtn(self):
        sel = self.vbtn_listbox.curselection()
        if sel:
            self.vbtn_manager.remove_button(sel[0])
            self._refresh_vbtn_list()

    def _add_vbtn_dialog(self):
        """Pop up a dialog to add a new virtual button."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Virtual Button")
        dlg.geometry("320x280")
        dlg.configure(bg=BG2)
        dlg.transient(self.root)
        dlg.grab_set()

        fields = {}
        for i, (lbl, default) in enumerate([
            ("Label (emoji/char):", "⏎"),
            ("Tooltip:", "Enter"),
            ("Action:", "key"),
            ("Value:", "enter"),
        ]):
            tk.Label(dlg, text=lbl, fg=FG, bg=BG2,
                     font=("Segoe UI", 10)).grid(row=i, column=0, padx=10, pady=6, sticky="w")
            var = tk.StringVar(value=default)
            entry = tk.Entry(dlg, textvariable=var, bg=BG3, fg=FG,
                             insertbackground=FG, font=("Segoe UI", 10),
                             relief="flat", width=20)
            entry.grid(row=i, column=1, padx=10, pady=6)
            fields[lbl] = var

        tk.Label(
            dlg, text="Actions: key, scroll, stt, hotkey, click, type",
            fg=FG_DIM, bg=BG2, font=("Segoe UI", 8)
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5))

        def add():
            self.vbtn_manager.add_button(
                label=fields["Label (emoji/char):"].get(),
                tooltip=fields["Tooltip:"].get(),
                action=fields["Action:"].get(),
                value=fields["Value:"].get(),
            )
            self._refresh_vbtn_list()
            dlg.destroy()

        tk.Button(
            dlg, text="Add", font=("Segoe UI", 10, "bold"),
            bg=ACCENT, fg=BG, relief="flat", padx=20, pady=6,
            command=add, cursor="hand2"
        ).grid(row=5, column=0, columnspan=2, pady=10)

    # ── FOOTER ───────────────────────────────────────────
    def _build_footer(self):
        frame = tk.Frame(self.root, bg=BG, pady=8)
        frame.pack(fill="x", side="bottom")

        tk.Label(
            frame, text="Right-click drag to reposition virtual buttons",
            font=("Segoe UI", 8), fg=FG_DIM, bg=BG
        ).pack()

        row = tk.Frame(frame, bg=BG)
        row.pack(pady=(5, 0))

        tk.Button(
            row, text="🎙️ Test STT", font=("Segoe UI", 9),
            bg=BG3, fg=FG, relief="flat", padx=10, pady=3,
            command=self._test_stt, cursor="hand2"
        ).pack(side="left", padx=5)

        tk.Button(
            row, text="Reconnect", font=("Segoe UI", 9),
            bg=BG3, fg=FG, relief="flat", padx=10, pady=3,
            command=self._reconnect, cursor="hand2"
        ).pack(side="left", padx=5)

    def _test_stt(self):
        if not is_listening():
            trigger_stt()

    def _reconnect(self):
        stop_serial_loop()
        self.root.after(500, self._start_serial)

    # ── SERIAL STARTUP ───────────────────────────────────
    def _start_serial(self):
        start_serial_loop()

    # ── STATUS UPDATER ───────────────────────────────────
    def _update_status(self):
        status = get_status()
        if status == "connected":
            self.status_dot.config(fg=GREEN)
            self.status_label.config(text="Connected")
        elif status == "error":
            self.status_dot.config(fg=RED)
            self.status_label.config(text="Error")
        else:
            self.status_dot.config(fg=RED)
            self.status_label.config(text="Disconnected")

        self.root.after(1000, self._update_status)

    # ── STT STATE CALLBACK (thread-safe) ─────────────────
    def _on_stt_state_safe(self, state):
        """Called from STT thread — schedule on main thread."""
        self.root.after(0, lambda: self._on_stt_state(state))

    def _on_stt_state(self, state):
        self.notification.on_stt_state(state)
        if state == "listening":
            self.stt_label.config(text="🎙️ Listening...", fg=ACCENT)
        elif state == "transcribing":
            self.stt_label.config(text="☁️ Transcribing...", fg=ORANGE)
        elif state == "typing":
            self.stt_label.config(text="⌨️ Typing...", fg=GREEN)
        elif state == "done":
            self.stt_label.config(text="✅ Done", fg=GREEN)
            self.root.after(3000, lambda: self.stt_label.config(text=""))
        elif state == "error":
            self.stt_label.config(text="❌ Error", fg=RED)
            self.root.after(3000, lambda: self.stt_label.config(text=""))

    # ── CLOSE ────────────────────────────────────────────
    def _on_close(self):
        stop_serial_loop()
        self.vbtn_manager.destroy_all()
        self.root.destroy()

    # ── RUN ──────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    app = AbleXApp()
    app.run()
