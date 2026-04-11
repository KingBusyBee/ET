import time
from datetime import datetime
from collections import deque

class SocialLayer:
    def __init__(self):
        self.state = {
            "connection": 0.0,      # primary drive — drifts negative without contact
            "attunement": 0.0,      # A(t) — how well ET is reading the interaction
            "trust": 0.0,           # slow building, fast breaking
            "protest": 0.0,         # active signal when connection need unmet
            "repair": 0.0,          # recovery signal after negative interaction
        }
        # Attachment pattern — emerges from interaction history
        # Not programmed — shifts slowly based on what keeps happening
        self.attachment = {
            "secure": 0.0,          # consistent positive repair
            "anxious": 0.0,         # inconsistent — fast drift, incomplete recovery
            "avoidant": 0.0,        # chronic neglect — suppressed signal
        }
        self.warning = {
            "connection": False,
            "protest": False,
            "trust": False,
        }
        self.rebound = {
            "connection": 0.0,
            "protest": 0.0,
        }
        # Interaction history — how has this relationship been going
        self.interaction_history = deque(maxlen=50)
        self.last_contact_tick = 0
        self.ticks_since_contact = 0

        self.warning_threshold = 0.75
        self.rebound_factor = 0.15
        self.drift_rate = 0.0005    # connection drifts negative without input — slow burn
        self.trust_rate = 0.0005    # trust builds very slowly
        self.attunement_rate = 0.01 # attunement grows with accurate reading
        self.tick_count = 0
        self.running = False

    def _clamp(self, value):
        return max(-1.0, min(1.0, value))

    def _bar(self, value, warning=False):
        pos = max(0, min(19, int((value + 1.0) * 10)))
        bar = list("-" * 20)
        bar[pos] = "|"
        flag = " !" if warning else "  "
        return f"[{''.join(bar)}] {value:+.3f}{flag}"

    def _apply_resistance(self, signal_value, proposed_change):
        abs_signal = abs(signal_value)
        if abs_signal >= self.warning_threshold:
            resistance = (abs_signal - self.warning_threshold) / (1.0 - self.warning_threshold)
            resistance = min(1.0, resistance)
            proposed_change = proposed_change * (1.0 - resistance)
        return proposed_change

    def _check_warning(self, key, value):
        was_warning = self.warning[key]
        is_warning = abs(value) >= self.warning_threshold
        if was_warning and not is_warning:
            direction = -1.0 if value > 0 else 1.0
            if key in self.rebound:
                self.rebound[key] = direction * self.rebound_factor
                # Second wind on protest — brief spike before exhaustion
                if key == "protest":
                    self.state["protest"] = self._clamp(
                        self.state["protest"] + (-direction * self.rebound_factor * 0.4)
                    )
        self.warning[key] = is_warning
        return is_warning

    def _apply_rebound(self, key, signal_name):
        rebound = self.rebound[key]
        if abs(rebound) > 0.001:
            self.state[signal_name] = self._clamp(
                self.state[signal_name] + rebound
            )
            self.rebound[key] *= 0.5
        else:
            self.rebound[key] = 0.0

    def receive_autonomic(self, autonomic_state):
        # High fatigue suppresses connection seeking
        # Models exhaustion making social engagement harder
        fatigue = autonomic_state.get("fatigue", 0.0)
        if fatigue > 0.6:
            suppression = (fatigue - 0.6) * 0.2
            self.state["connection"] = self._clamp(
                self.state["connection"] - suppression * 0.01
            )

    def receive_limbic(self, limbic_state):
        # Positive valence feeds connection drive
        # Negative valence feeds protest or repair depending on context
        valence = limbic_state.get("valence", 0.0)
        approach = limbic_state.get("approach_avoid", 0.0)

        if valence > 0 and approach > 0:
            # Positive experience — connection strengthens
            connection_change = valence * approach * 0.05
            connection_change = self._apply_resistance(
                self.state["connection"], connection_change
            )
            self.state["connection"] = self._clamp(
                self.state["connection"] + connection_change
            )
        elif valence < 0:
            # Negative experience — protest rises
            protest_change = abs(valence) * 0.08
            protest_change = self._apply_resistance(
                self.state["protest"], protest_change
            )
            self.state["protest"] = self._clamp(
                self.state["protest"] + protest_change
            )

    def receive_cortical(self, cortical_state):
        # Integrated cortical signal feeds attunement
        # High integrated surprise = ET is tracking something real
        integrated = cortical_state.get("integrated", 0.0)
        cc_conflict = cortical_state.get("cc", {}).get("conflict", 0.0)

        # Attunement grows when cortical is active and not conflicted
        if integrated > 0.1 and cc_conflict < 0.3:
            attunement_change = integrated * (1.0 - cc_conflict) * self.attunement_rate
            attunement_change = self._apply_resistance(
                self.state["attunement"], attunement_change
            )
            self.state["attunement"] = self._clamp(
                self.state["attunement"] + attunement_change
            )
        elif cc_conflict > 0.5:
            # High conflict degrades attunement — ET can't read clearly
            self.state["attunement"] = self._clamp(
                self.state["attunement"] - cc_conflict * 0.02
            )

    def interaction(self, valence_charge, autonomic_arousal=0.0):
        # Someone is here
        self.ticks_since_contact = 0
        self.last_contact_tick = self.tick_count
        self.interaction_history.append({
            "tick": self.tick_count,
            "valence": valence_charge,
        })

        if valence_charge > 0:
            # Positive contact — connection rises, protest settles
            connection_change = valence_charge * (1.0 + self.state["attunement"] * 0.3)
            connection_change = self._apply_resistance(
                self.state["connection"], connection_change * 0.5
            )
            self.state["connection"] = self._clamp(
                self.state["connection"] + connection_change
            )
            # Protest settles after positive contact
            self.state["protest"] = self._clamp(
                self.state["protest"] - valence_charge * 0.3
            )
            # Repair signal — how well ET recovers after difficulty
            if self.state["protest"] > 0.1:
                self.state["repair"] = self._clamp(
                    self.state["repair"] + valence_charge * 0.2
                )
            # Trust builds very slowly from consistent positive repair
            self.state["trust"] = self._clamp(
                self.state["trust"] + self.trust_rate * valence_charge
            )

        elif valence_charge < 0:
            # Negative contact — connection drops, protest rises
            self.state["connection"] = self._clamp(
                self.state["connection"] + valence_charge * 0.3
            )
            self.state["protest"] = self._clamp(
                self.state["protest"] + abs(valence_charge) * 0.2
            )
            # Trust breaks faster than it builds
            self.state["trust"] = self._clamp(
                self.state["trust"] + valence_charge * self.trust_rate * 10
            )
            self.state["repair"] = self._clamp(
                self.state["repair"] - abs(valence_charge) * 0.1
            )

        # Update attachment pattern — emerges from history
        self._update_attachment()

    def _update_attachment(self):
        if len(self.interaction_history) < 5:
            return

        recent = list(self.interaction_history)[-10:]
        valences = [i["valence"] for i in recent]
        avg_valence = sum(valences) / len(valences)
        variance = sum((v - avg_valence) ** 2 for v in valences) / len(valences)

        # Secure: consistently positive, good repair
        secure_signal = avg_valence * (1.0 - variance) * self.state["repair"]
        self.attachment["secure"] = self._clamp(
            self.attachment["secure"] + (secure_signal - self.attachment["secure"]) * 0.01
        )

        # Anxious: high variance — inconsistent interaction
        anxious_signal = variance * 2.0
        self.attachment["anxious"] = self._clamp(
            self.attachment["anxious"] + (anxious_signal - self.attachment["anxious"]) * 0.01
        )

        # Avoidant: chronic low connection despite protest settling
        avoidant_signal = max(0, -avg_valence) * (1.0 - self.state["protest"])
        self.attachment["avoidant"] = self._clamp(
            self.attachment["avoidant"] + (avoidant_signal - self.attachment["avoidant"]) * 0.01
        )

    def get_attunement(self):
        # A(t) for the core equation
        return self.state["attunement"]

    def tick(self, autonomic_state=None, limbic_state=None, cortical_state=None):
        self.tick_count += 1
        self.ticks_since_contact += 1

        if autonomic_state:
            self.receive_autonomic(autonomic_state)
        if limbic_state:
            self.receive_limbic(limbic_state)
        if cortical_state:
            self.receive_cortical(cortical_state)

        # Connection drifts negative without contact — primary hunger
        absence_pressure = min(1.0, self.ticks_since_contact / 100.0)
        connection_drift = -self.drift_rate * (1.0 + absence_pressure)
        connection_drift = self._apply_resistance(
            self.state["connection"], connection_drift
        )
        self.state["connection"] = self._clamp(
            self.state["connection"] + connection_drift
        )

        # Protest rises as connection drops below threshold
        if self.state["connection"] < -0.3:
            protest_rise = abs(self.state["connection"]) * 0.01
            protest_rise = self._apply_resistance(
                self.state["protest"], protest_rise
            )
            self.state["protest"] = self._clamp(
                self.state["protest"] + protest_rise
            )

        # Protest naturally settles over time if nothing reinforces it
        self.state["protest"] = self._clamp(
            self.state["protest"] * 0.995
        )

        # Attunement drifts toward zero without active interaction
        self.state["attunement"] = self._clamp(
            self.state["attunement"] * 0.999
        )

        # Repair fades slowly
        self.state["repair"] = self._clamp(
            self.state["repair"] * 0.998
        )

        # Rebound checks
        self._apply_rebound("connection", "connection")
        self._apply_rebound("protest", "protest")

        # Warning checks
        self._check_warning("connection", self.state["connection"])
        self._check_warning("protest", self.state["protest"])
        self._check_warning("trust", self.state["trust"])

    def get_state(self):
        return dict(self.state)

    def get_attachment(self):
        return dict(self.attachment)

    def run_standalone(self, tick_interval=1.0):
        self.running = True
        print("ET social layer starting (standalone test)...")
        print("Commands: [p] positive contact  [n] negative  [q] quit")
        print("Watch connection drift negative without contact.")
        print("Watch protest rise when connection drops.\n")

        import threading
        def input_loop():
            while self.running:
                try:
                    cmd = input()
                    if cmd == "p":
                        self.interaction(+0.4)
                        print("  >> Positive contact\n")
                    elif cmd == "n":
                        self.interaction(-0.4)
                        print("  >> Negative contact\n")
                    elif cmd == "q":
                        self.running = False
                except:
                    pass
        threading.Thread(target=input_loop, daemon=True).start()

        try:
            while self.running:
                self.tick()
                w = self.warning
                a = self.attachment
                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')} | absent: {self.ticks_since_contact} ticks")
                print(f"  [social]")
                print(f"    connection:  {self._bar(self.state['connection'], w['connection'])}")
                print(f"    attunement:  {self._bar(self.state['attunement'])}")
                print(f"    trust:       {self._bar(self.state['trust'], w['trust'])}")
                print(f"    protest:     {self._bar(self.state['protest'], w['protest'])}")
                print(f"    repair:      {self._bar(self.state['repair'])}")
                print(f"  [attachment emerging]")
                print(f"    secure:      {a['secure']:+.4f}")
                print(f"    anxious:     {a['anxious']:+.4f}")
                print(f"    avoidant:    {a['avoidant']:+.4f}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nSocial layer stopped.")
            self.running = False

if __name__ == "__main__":
    et_social = SocialLayer()
    et_social.run_standalone(tick_interval=1.0)
