import tkinter as tk
import threading
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from et_core import ETCore
from story_reader import read_to_et

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

        # Scrollable conversation area
        self.conversation_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.conversation_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(8, 0))

        self.conversation = tk.Text(
            self.conversation_frame,
            font=("Helvetica", 11),
            bg="#0a0a0a",
            fg="#555555",
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=8,
            cursor="arrow",
        )
        self.conversation.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(
            self.conversation_frame,
            command=self.conversation.yview,
            bg="#0a0a0a",
            troughcolor="#0a0a0a",
            width=4
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.conversation.config(yscrollcommand=scrollbar.set)

        # Color tags
        self.conversation.tag_configure("et", foreground="#666666", font=("Helvetica", 11, "italic"))
        self.conversation.tag_configure("you", foreground="#444444", font=("Helvetica", 11))
        self.conversation.tag_configure("system", foreground="#2a2a2a", font=("Helvetica", 9))

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

        # Dashboard — three numbers, barely visible
        self.dashboard_var = tk.StringVar(value="")
        self.dashboard_label = tk.Label(
            self.root,
            textvariable=self.dashboard_var,
            font=("Helvetica", 9),
            bg="#0a0a0a",
            fg="#2a2a2a",
            justify=tk.CENTER
        )
        self.dashboard_label.pack(side=tk.BOTTOM, pady=(0, 2))

        # Subtle status line
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 10),
            bg="#0a0a0a",
            fg="#333333"
        )
        self.status_label.pack(side=tk.BOTTOM, pady=(0, 2))

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

        # Start reading Swimmer to ET — one sentence every 12 seconds
        # ET doesn't understand yet — words land with current signal state
        self.story_thread = read_to_et(self.et, interval=8.0, repeat=True, verbose=True)

        # Update display on main thread
        self.root.after(100, self.update_display)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        import signal
        signal.signal(signal.SIGINT, lambda s, f: self.on_close())

    def on_keypress(self, event):
        # Every keystroke = small presence signal
        if event.char and event.char.isprintable():
            threading.Thread(
                target=lambda: self.et.interaction(0.02),
                daemon=True
            ).start()

    def _add_to_conversation(self, text, tag="system"):
        self.conversation.config(state=tk.NORMAL)
        self.conversation.insert(tk.END, text + "\n", tag)
        self.conversation.see(tk.END)
        self.conversation.config(state=tk.DISABLED)

    def on_input(self, event):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")

        # Show what you typed in the conversation
        self._add_to_conversation(text, tag="you")

        # Text length = signal strength, capped at 0.4
        charge = min(0.4, len(text) * 0.02)

        def send():
            self.et.interaction(charge)
            self.et.social.ticks_since_contact = 0
            # Your words go into ET's language systems
            with self.et.lock:
                valence = self.et.limbic.state.get("valence", 0.0)
                arousal = self.et.autonomic.state.get("arousal", 0.0)
                attention = self.et.cortical.get_attention()
                self.et.word_store.hear(text, valence, arousal, self.et.tick_count)
                self.et.cooc.learn(text, valence, arousal, attention)

        threading.Thread(target=send, daemon=True).start()

    def run_et(self):
        while self.running:
            self.et.tick()
            time.sleep(0.1)

    def _get_attention_eyes(self, cortical, social_state):
        # Eyes emerge from attention signal and direction
        # Direction shows which hemisphere is leading
        attention = cortical.get_attention()
        direction = cortical.get_attention_direction()
        soc_firing = cortical.left["soc_firing"] or cortical.right["soc_firing"]

        if soc_firing:
            return "◉ ◉"       # SOC firing — full alert
        elif direction == "none" or attention < 0.05:
            return " "          # resting — not attending
        elif direction == "left":
            return "◉ ○"       # left dominant — pattern/language focus
        elif direction == "right":
            return "○ ◉"       # right dominant — spatial/intuitive focus
        elif direction == "balanced" and attention > 0.2:
            return "◉ ◉"       # balanced high attention
        else:
            return "○ ○"       # soft balanced attention

    def update_display(self):
        if not self.running:
            return
        try:
            # Sleep overrides face
            if self.et.sleep_system.sleeping:
                depth = self.et.sleep_system.sleep_depth
                if depth > 0.5:
                    face = "😴"
                else:
                    face = "😪"
            else:
                face = self.et._get_face()
            self.face_var.set(face)

            eyes = self._get_attention_eyes(
                self.et.cortical,
                self.et.social.get_state()
            )
            self.eyes_var.set(eyes)

            # Very subtle tick counter
            self.tick_var.set(f"· {self.et.tick_count} ·")

            # ET utterance — add to conversation if new
            if self.et._last_utterance and self.et._last_utterance != getattr(self, "_displayed_utterance", None):
                self._displayed_utterance = self.et._last_utterance
                self._add_to_conversation(f"{self.et._last_utterance}", tag="et")

            # Dashboard — episodes, attachment, words
            mem = self.et.memory.summary()
            att = self.et.social.attachment
            words = self.et.word_store.summary()
            dominant_attachment = max(att, key=att.get)
            attachment_val = att[dominant_attachment]
            ep_count = mem.get("total_episodes", 0) if isinstance(mem, dict) else 0
            word_count = words.get("total_words", 0)
            sleep_state = self.et.sleep_system
            sleep_str = f"z{sleep_state.cycles}" if sleep_state.sleeping else f"r{sleep_state.cycles}"
            self.dashboard_var.set(
                f"mem:{ep_count}  words:{word_count}  {sleep_str}"
            )

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
        self.et.memory.save()
        self.et.word_store.save()
        self.et.hippocampus.save(self.et.hippocampus_path)
        self.et.cooc.save()
        try:
            self.root.destroy()
        except:
            pass

    def on_interrupt(self):
        self.on_close()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ETWindow()
    app.run()
