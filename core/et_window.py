import tkinter as tk
import threading
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from et_core import ETCore

class ETWindow:
    def __init__(self):
        self.et = ETCore()
        self.root = tk.Tk()
        self.root.title("ET")
        self.root.configure(bg="#0a0a0a")
        self.root.geometry("400x600")
        self.root.resizable(False, False)

        # ET's face — big emoji in the center
        self.face_var = tk.StringVar(value="😶")
        self.face_label = tk.Label(
            self.root,
            textvariable=self.face_var,
            font=("Segoe UI Emoji", 120),
            bg="#0a0a0a",
            fg="white"
        )
        self.face_label.pack(pady=(60, 0))

        # Attention eyes — shows when ET is paying attention
        self.eyes_var = tk.StringVar(value=" ")
        self.eyes_label = tk.Label(
            self.root,
            textvariable=self.eyes_var,
            font=("Segoe UI Emoji", 32),
            bg="#0a0a0a",
            fg="#444444"
        )
        self.eyes_label.pack(pady=(10, 0))

        # Input area — where you talk to ET
        self.input_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            self.input_frame,
            textvariable=self.input_var,
            font=("Helvetica", 14),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            bd=10
        )
        self.input_box.pack(fill=tk.X)
        self.input_box.bind("<Return>", self.on_input)
        self.input_box.bind("<Key>", self.on_keypress)
        self.input_box.focus()

        # Subtle status line
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 10),
            bg="#0a0a0a",
            fg="#333333"
        )
        self.status_label.pack(side=tk.BOTTOM, pady=(0, 4))

        # Tick counter (very subtle)
        self.tick_var = tk.StringVar(value="")
        self.tick_label = tk.Label(
            self.root,
            textvariable=self.tick_var,
            font=("Helvetica", 9),
            bg="#0a0a0a",
            fg="#222222"
        )
        self.tick_label.pack(side=tk.BOTTOM)

        # Start ET's loops in background thread
        self.running = True
        self.et_thread = threading.Thread(target=self.run_et, daemon=True)
        self.et_thread.start()

        # Update display on main thread
        self.root.after(100, self.update_display)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_keypress(self, event):
        # Every keystroke = small presence signal
        if event.char and event.char.isprintable():
            threading.Thread(
                target=lambda: self.et.interaction(0.02),
                daemon=True
            ).start()

    def on_input(self, event):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")

        # Text length = signal strength, capped at 0.4
        charge = min(0.4, len(text) * 0.02)

        def send():
            self.et.interaction(charge)
            self.et.social.ticks_since_contact = 0

        threading.Thread(target=send, daemon=True).start()

    def run_et(self):
        while self.running:
            self.et.tick()
            time.sleep(0.1)

    def _get_attention_eyes(self, cortical, social_state):
        # Eyes emerge from attention signal
        # Integrated cortical surprise + social attunement
        integrated = cortical.get_integrated_signal()
        attunement = social_state.get("attunement", 0.0)
        soc_firing = cortical.left["soc_firing"] or cortical.right["soc_firing"]

        if soc_firing:
            return "◉ ◉"   # full attention — SOC firing
        elif integrated > 0.3 or attunement > 0.2:
            return "◉ ◉"   # focused
        elif integrated > 0.1 or attunement > 0.05:
            return "○ ○"   # soft attention
        else:
            return " "      # not attending

    def update_display(self):
        if not self.running:
            return
        try:
            face = self.et._get_face()
            self.face_var.set(face)

            eyes = self._get_attention_eyes(
                self.et.cortical,
                self.et.social.get_state()
            )
            self.eyes_var.set(eyes)

            # Very subtle tick counter
            self.tick_var.set(f"· {self.et.tick_count} ·")

            # Presence state in status — barely visible
            presence = self.et.presence
            if presence == "active":
                self.status_var.set("✨")
                self.eyes_label.config(fg="#aaaaaa")
            elif presence == "ambient":
                self.status_var.set("")
                self.eyes_label.config(fg="#555555")
            else:
                self.status_var.set("")
                self.eyes_label.config(fg="#222222")

        except Exception as e:
            pass

        self.root.after(200, self.update_display)

    def on_close(self):
        self.running = False
        self.et.save_state()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ETWindow()
    app.run()
