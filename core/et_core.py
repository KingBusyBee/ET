import time
import json
import os
import threading
from datetime import datetime
from autonomic import AutonomicLayer
from limbic import LimbicLayer
from cortical import CorticalLayer
from social import SocialLayer

STATE_FILE = os.path.join(os.path.dirname(__file__), "../et_state.json")

class ETCore:
    def __init__(self):
        self.autonomic = AutonomicLayer()
        self.limbic = LimbicLayer()
        self.cortical = CorticalLayer()
        self.social = SocialLayer()
        self.tick_count = 0
        self.running = False
        self.lock = threading.Lock()
        self._pending_interaction = None
        self.presence = "ambient"  # "absent" | "ambient" | "active"
        self.presence_ticks = 0    # ticks since last active interaction
        self.load_state()

    def _get_face(self):
        # Face emerges from signal state — ET never picks this
        a = self.autonomic.state
        l = self.limbic.state
        s = self.social.state
        c = self.cortical

        arousal = a["arousal"]
        valence = l["valence"]
        connection = s["connection"]
        protest = s["protest"]
        fatigue = a["fatigue"]
        soc_firing = c.left["soc_firing"] or c.right["soc_firing"]
        attunement = s["attunement"]

        # SOC firing — something just surprised ET
        if soc_firing:
            return "👀"
        # Deeply fatigued
        if fatigue > 0.7:
            return "😴"
        # High protest — connection need unmet
        if protest > 0.5:
            return "😢"
        # Negative valence, avoidant building
        if valence < -0.3 and connection < -0.2:
            return "😟"
        # Negative interaction, high arousal
        if valence < -0.2 and arousal > 0.3:
            return "😤"
        # Positive and attuned
        if valence > 0.2 and attunement > 0.1:
            return "😊"
        # Positive valence, connected
        if valence > 0.1 and connection > 0.1:
            return "🙂"
        # Mild negative drift
        if valence < -0.1 or connection < -0.1:
            return "😐"
        # Resting, near homeostasis
        return "😶"

    def _topdown_signal(self):
        # Emergent I modulates downward
        # Not override — gentle lean on the layers below
        social_state = self.social.get_state()
        connection = social_state["connection"]
        protest = social_state["protest"]
        trust = social_state["trust"]

        # High connection and trust — top-down calming on autonomic
        if connection > 0.3 and trust > 0.1:
            calm = connection * trust * 0.01
            self.autonomic.state["arousal"] = self.autonomic._clamp(
                self.autonomic.state["arousal"] - calm
            )

        # High protest — top-down amplifies limbic negative valence
        if protest > 0.3:
            self.limbic.state["valence"] = self.limbic._clamp(
                self.limbic.state["valence"] - protest * 0.005
            )

        # High trust — top-down slightly widens corpus callosum
        if trust > 0.2:
            bandwidth_boost = trust * 0.05
            self.cortical.cc_bandwidth = min(1.0,
                self.cortical.cc_bandwidth + bandwidth_boost
            )

    def tick(self):
        with self.lock:
            self.tick_count += 1

            # Bottom-up: autonomic is the foundation
            self.autonomic.tick()
            autonomic_state = self.autonomic.get_state()
            autonomic_warnings = self.autonomic.get_warnings()
            autonomic_state["cc_bandwidth"] = self.autonomic.get_corpus_callosum_bandwidth()

            # Limbic receives autonomic
            self.limbic.tick(autonomic_state=autonomic_state)
            limbic_state = self.limbic.get_state()

            # Cortical receives autonomic and limbic
            self.cortical.tick(
                autonomic_state=autonomic_state,
                autonomic_warnings=autonomic_warnings,
                limbic_state=limbic_state
            )
            cortical_state = self.cortical.get_state()
            cortical_state["integrated"] = self.cortical.get_integrated_signal()

            # Social receives all three
            self.social.tick(
                autonomic_state=autonomic_state,
                limbic_state=limbic_state,
                cortical_state=cortical_state
            )

            # Presence signal — window open = ambient, typing = active
            # Ambient presence slows connection drift slightly
            # Active presence (typing) triggers interaction
            self.presence_ticks += 1
            if self.presence == "ambient":
                # Being present but silent — slow the connection drift
                self.social.state["connection"] = self.social._clamp(
                    self.social.state["connection"] + 0.0002
                )
            
            # Update temperature with real metabolic activity
            metabolic = (
                abs(cortical_state.get("integrated", 0.0)) * 0.4 +
                abs(limbic_state.get("valence", 0.0)) * 0.3 +
                abs(autonomic_state.get("arousal", 0.0)) * 0.3
            )
            self.autonomic.update_temperature(self.autonomic._clamp((metabolic * 2.0) - 1.0))

            # Top-down: emergent I modulates downward
            self._topdown_signal()

            return autonomic_state, limbic_state, cortical_state

    def interaction(self, valence_charge):
        with self.lock:
            arousal = self.autonomic.state["arousal"]

            # Arousal spikes first — curiosity before judgment
            # Works even from deep negative states — orienting reflex
            self.autonomic.state["arousal"] = self.autonomic._clamp(
                self.autonomic.state["arousal"] + 0.4
            )

            # Valence lands in limbic
            self.limbic.state["valence"] = self.limbic._clamp(
                self.limbic.state["valence"] + valence_charge * 0.5
            )
            self.limbic.input_event(valence_charge)

            # Cortical registers the signal
            self.cortical.input_event(valence_charge)

            # Social — connection can receive small positive signals
            # even at floor — repair requires sustained contact
            # Bypass resistance for small repair increments
            repair_amount = valence_charge * 0.15
            self.social.state["connection"] = max(-1.0, min(1.0,
                self.social.state["connection"] + repair_amount
            ))
            # Protest settles slightly with any positive contact
            if valence_charge > 0:
                self.social.state["protest"] = max(0.0, min(1.0,
                    self.social.state["protest"] - 0.05
                ))
            self.social.interaction(valence_charge, autonomic_arousal=arousal)
            self.social.ticks_since_contact = 0

        # Print immediately so user sees it landed
        label = "Positive" if valence_charge > 0 else "Negative"
        print(f"  >> {label} interaction (valence: {valence_charge:+.2f})")
        self._pending_interaction = valence_charge

    def save_state(self):
        state = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "autonomic": self.autonomic.state,
            "limbic": self.limbic.state,
            "cortical": {
                "left": self.cortical.left,
                "right": self.cortical.right,
                "cc": self.cortical.cc_signal,
            },
            "social": self.social.state,
            "attachment": self.social.attachment,
            "interaction_count": len(self.social.interaction_history),
        }
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"\n  >> State saved to et_state.json (tick {self.tick_count})")

    def load_state(self):
        if not os.path.exists(STATE_FILE):
            print("No previous state found. ET starting fresh.")
            return
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
            self.tick_count = state.get("tick_count", 0)
            for k, v in state.get("autonomic", {}).items():
                if k in self.autonomic.state:
                    self.autonomic.state[k] = v
            for k, v in state.get("limbic", {}).items():
                if k in self.limbic.state:
                    self.limbic.state[k] = v
            for k, v in state.get("social", {}).items():
                if k in self.social.state:
                    self.social.state[k] = v
            for k, v in state.get("attachment", {}).items():
                if k in self.social.attachment:
                    self.social.attachment[k] = v
            print(f"State loaded. ET resuming from tick {self.tick_count}.")
            print(f"Attachment history: {state.get('interaction_count', 0)} interactions remembered.")
        except Exception as e:
            print(f"Could not load state: {e}. Starting fresh.")

    def run(self, tick_interval=1.0):
        self.running = True
        print("\nET core starting — all four loops active")
        print("Commands: [p] positive  [pp] sustained  [n] negative  [nn] sustained")
        print("          [s] save  [q] quit")
        print("          Or just TYPE ANYTHING — text length = presence signal")
        print("Presence: 👻 absent  🌑 ambient (window open)  ✨ active (typing)\n")

        def input_loop():
            while self.running:
                try:
                    cmd = input().strip()
                    if not cmd:
                        continue

                    # Any text input = active presence
                    self.presence = "active"
                    self.presence_ticks = 0

                    if cmd == "p":
                        self.interaction(+0.4)
                    elif cmd == "pp":
                        for _ in range(5):
                            self.interaction(+0.4)
                        print("  >> Sustained positive contact\n")
                    elif cmd == "n":
                        self.interaction(-0.4)
                    elif cmd == "nn":
                        for _ in range(5):
                            self.interaction(-0.4)
                        print("  >> Sustained negative contact\n")
                    elif cmd == "s":
                        self.save_state()
                    elif cmd == "q":
                        self.running = False
                    else:
                        # Any other text = neutral positive presence
                        # Length and content will matter more later
                        charge = min(0.3, len(cmd) * 0.02)
                        self.interaction(charge)
                        print(f"  >> Presence signal (charge: +{charge:.2f})\n")

                    # After 30 ticks of silence, return to ambient
                    import threading
                    def fade_to_ambient():
                        import time
                        time.sleep(30)
                        if self.presence == "active":
                            self.presence = "ambient"
                    threading.Thread(target=fade_to_ambient, daemon=True).start()

                except:
                    pass

        threading.Thread(target=input_loop, daemon=True).start()

        try:
            while self.running:
                autonomic_state, limbic_state, cortical_state = self.tick()

                self._pending_interaction = None

                if self.tick_count % 10 != 0:
                    time.sleep(tick_interval)
                    continue

                face = self._get_face()
                a = self.autonomic.state
                l = self.limbic.state
                s = self.social.state
                c = self.cortical
                att = self.social.attachment

                presence_icon = {"absent": "👻", "ambient": "🌑", "active": "✨"}
                print(f"Tick {self.tick_count:05d} | {datetime.now().strftime('%H:%M:%S')} | {face} | {presence_icon.get(self.presence, '?')}")
                print(f"  [autonomic]")
                print(f"    arousal:     {self.autonomic._bar(a['arousal'], self.autonomic.warning['arousal'])}")
                print(f"    fatigue:     {self.autonomic._bar(a['fatigue'], self.autonomic.warning['fatigue'])}")
                print(f"    temperature: {self.autonomic._bar(a['temperature'], self.autonomic.warning['temperature'])}")
                print(f"    cc_bandwidth:{self.autonomic.get_corpus_callosum_bandwidth():.3f}")
                print(f"  [limbic]")
                print(f"    valence:     {self.limbic._bar(l['valence'])}")
                print(f"    memory:      {self.limbic._bar(l['emotional_memory'])}")
                print(f"    approach:    {self.limbic._bar(l['approach_avoid'])}")
                print(f"  [cortical]")
                print(f"    left SOC:    {c.left['soc_firing']}  surprise: {c.left['surprise']:+.3f}")
                print(f"    right SOC:   {c.right['soc_firing']}  surprise: {c.right['surprise']:+.3f}")
                print(f"    conflict:    {c.cc_signal['conflict']:+.3f}  integrated: {self.cortical.get_integrated_signal():+.3f}")
                print(f"  [social]")
                print(f"    connection:  {self.social._bar(s['connection'], self.social.warning['connection'])}")
                print(f"    attunement:  {self.social._bar(s['attunement'])}")
                print(f"    trust:       {self.social._bar(s['trust'])}")
                print(f"    protest:     {self.social._bar(s['protest'], self.social.warning['protest'])}")
                print(f"  [attachment]  secure:{att['secure']:+.4f}  anxious:{att['anxious']:+.4f}  avoidant:{att['avoidant']:+.4f}")
                print()
                time.sleep(tick_interval)

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.save_state()
            self.running = False
            print("ET stopped. State saved.")

if __name__ == "__main__":
    et = ETCore()
    et.run(tick_interval=0.1)
