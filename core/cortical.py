import time
from datetime import datetime
from collections import deque

class CorticalLayer:
    def __init__(self):
        # Two distinct loops
        self.left = {
            "prediction": 0.0,    # what left expects next
            "confidence": 0.0,    # how sure left is
            "surprise": 0.0,      # mismatch from prediction
            "soc_firing": False,  # SOC threshold crossed
        }
        self.right = {
            "prediction": 0.0,    # what right expects next
            "confidence": 0.0,    # how sure right is
            "surprise": 0.0,      # mismatch from prediction
            "soc_firing": False,  # SOC threshold crossed
        }
        # Corpus callosum — bandwidth set by autonomic
        self.cc_bandwidth = 1.0
        self.cc_signal = {
            "left_to_right": 0.0,  # what left is sending right
            "right_to_left": 0.0,  # what right is sending left
            "conflict": 0.0,       # disagreement between hemispheres
        }
        # Warning and rebound — same architecture as autonomic
        self.warning = {
            "left_surprise": False,
            "right_surprise": False,
            "conflict": False,
        }
        self.rebound = {
            "left_surprise": 0.0,
            "right_surprise": 0.0,
        }
        # Prediction history — short term pattern memory
        self.left_history = deque(maxlen=10)
        self.right_history = deque(maxlen=10)

        self.soc_threshold = 0.6      # surprise level that fires a SOC
        self.warning_threshold = 0.75
        self.rebound_factor = 0.15
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
        self.warning[key] = is_warning
        return is_warning

    def _apply_rebound(self, key, signal_name, loop):
        rebound = self.rebound[key]
        if abs(rebound) > 0.001:
            loop[signal_name] = self._clamp(loop[signal_name] + rebound)
            self.rebound[key] *= 0.5
        else:
            self.rebound[key] = 0.0

    def receive_autonomic(self, autonomic_state, autonomic_warnings):
        # Corpus callosum bandwidth driven by autonomic arousal
        self.cc_bandwidth = autonomic_state.get("cc_bandwidth", 1.0)

        # High fatigue degrades prediction confidence in both loops
        fatigue = autonomic_state.get("fatigue", 0.0)
        if fatigue > 0.5:
            degradation = (fatigue - 0.5) * 0.1
            self.left["confidence"] = self._clamp(
                self.left["confidence"] - degradation
            )
            self.right["confidence"] = self._clamp(
                self.right["confidence"] - degradation
            )

    def receive_limbic(self, limbic_state):
        # Valence biases prediction
        # Positive valence — left gets optimistic predictions
        # Negative valence — right gets cautious spatial alertness
        valence = limbic_state.get("valence", 0.0)
        if valence > 0:
            self.left["prediction"] = self._clamp(
                self.left["prediction"] + valence * 0.05
            )
        else:
            self.right["prediction"] = self._clamp(
                self.right["prediction"] + valence * 0.05
            )

    def input_event(self, signal_value):
        # New input arrives — both loops compute surprise
        # Left processes it analytically — compares to pattern history
        # Right processes it spatially — compares to felt expectation

        # Left surprise — how different from recent pattern average
        if len(self.left_history) > 0:
            left_expected = sum(self.left_history) / len(self.left_history)
            left_surprise = abs(signal_value - left_expected)
        else:
            left_surprise = abs(signal_value) * 0.5
        self.left_history.append(signal_value)

        # Right surprise — how different from current prediction
        right_surprise = abs(signal_value - self.right["prediction"])
        self.right_history.append(signal_value)

        # Apply resistance before updating
        left_change = self._apply_resistance(
            self.left["surprise"],
            (left_surprise - self.left["surprise"]) * 0.4
        )
        self.left["surprise"] = self._clamp(self.left["surprise"] + left_change)

        right_change = self._apply_resistance(
            self.right["surprise"],
            (right_surprise - self.right["surprise"]) * 0.4
        )
        self.right["surprise"] = self._clamp(self.right["surprise"] + right_change)

        # SOC check — does surprise cross threshold?
        self.left["soc_firing"] = self.left["surprise"] >= self.soc_threshold
        self.right["soc_firing"] = self.right["surprise"] >= self.soc_threshold

        # Update predictions toward actual
        self.left["prediction"] = self._clamp(
            self.left["prediction"] + (signal_value - self.left["prediction"]) * 0.2
        )
        self.right["prediction"] = self._clamp(
            self.right["prediction"] + (signal_value - self.right["prediction"]) * 0.3
        )

        # Confidence builds with consistent input
        self.left["confidence"] = self._clamp(self.left["confidence"] + 0.05)
        self.right["confidence"] = self._clamp(self.right["confidence"] + 0.03)

    def _update_corpus_callosum(self):
        # Hemispheres share their surprise signal
        # Bandwidth determines how much gets through
        self.cc_signal["left_to_right"] = self._clamp(
            self.left["surprise"] * self.cc_bandwidth
        )
        self.cc_signal["right_to_left"] = self._clamp(
            self.right["surprise"] * self.cc_bandwidth
        )
        # Conflict — how much do the two loops disagree
        self.cc_signal["conflict"] = abs(
            self.left["surprise"] - self.right["surprise"]
        ) * self.cc_bandwidth

        # Each loop is slightly influenced by what it receives
        self.left["prediction"] = self._clamp(
            self.left["prediction"] + self.cc_signal["right_to_left"] * 0.1
        )
        self.right["prediction"] = self._clamp(
            self.right["prediction"] + self.cc_signal["left_to_right"] * 0.1
        )

    def tick(self, autonomic_state=None, autonomic_warnings=None, limbic_state=None):
        self.tick_count += 1

        if autonomic_state:
            self.receive_autonomic(autonomic_state, autonomic_warnings or {})
        if limbic_state:
            self.receive_limbic(limbic_state)

        # Surprise naturally decays back toward zero without input
        self.left["surprise"] = self._clamp(
            self.left["surprise"] * 0.92
        )
        self.right["surprise"] = self._clamp(
            self.right["surprise"] * 0.92
        )

        # Rebound check
        self._apply_rebound("left_surprise", "surprise", self.left)
        self._apply_rebound("right_surprise", "surprise", self.right)

        # Warning checks
        self._check_warning("left_surprise", self.left["surprise"])
        self._check_warning("right_surprise", self.right["surprise"])
        self._check_warning("conflict", self.cc_signal["conflict"])

        # Update corpus callosum
        self._update_corpus_callosum()

    def get_state(self):
        return {
            "left": dict(self.left),
            "right": dict(self.right),
            "cc": dict(self.cc_signal),
            "cc_bandwidth": self.cc_bandwidth,
        }

    def get_warnings(self):
        return dict(self.warning)

    def get_integrated_signal(self):
        # What rises to the social layer
        # Weighted by confidence and bandwidth
        left_weight = (self.left["confidence"] + 1.0) / 2.0
        right_weight = (self.right["confidence"] + 1.0) / 2.0
        total = left_weight + right_weight
        if total == 0:
            return 0.0
        integrated = (
            (self.left["surprise"] * left_weight) +
            (self.right["surprise"] * right_weight)
        ) / total
        # Conflict degrades the integration
        integrated = integrated * (1.0 - self.cc_signal["conflict"] * 0.3)
        return self._clamp(integrated)


    def get_attention(self):
        # Attention emerges from surprise, confidence, and conflict
        # Not a command — a readable state other loops can notice
        # High surprise + low conflict = focused attention
        # High conflict = scattered, fragmented attention
        # Low surprise = resting attention
        left_surprise = self.left["surprise"]
        right_surprise = self.right["surprise"]
        conflict = self.cc_signal["conflict"]
        left_confidence = self.left["confidence"]
        right_confidence = self.right["confidence"]

        # Weighted surprise — confidence amplifies the signal
        weighted_surprise = (
            (left_surprise * (left_confidence + 1.0) / 2.0) +
            (right_surprise * (right_confidence + 1.0) / 2.0)
        ) / 2.0

        # Conflict degrades attention quality
        # Internal disagreement = scattered focus
        attention = weighted_surprise * (1.0 - conflict * 0.5)

        # Attention has momentum — doesn't spike and vanish instantly
        # Models the fact that attention lingers after surprise fades
        if not hasattr(self, "_attention"):
            self._attention = 0.0
        self._attention = self._clamp(
            self._attention + (attention - self._attention) * 0.15
        )
        return self._attention

    def get_attention_direction(self):
        # What is attention pointing at?
        # Emerges from which loop is more active
        # Returns: "left" (pattern/language focus)
        #          "right" (spatial/intuitive focus)
        #          "balanced" (integrated)
        #          "none" (resting)
        attention = self.get_attention()
        if attention < 0.05:
            return "none"
        left = self.left["surprise"] * (self.left["confidence"] + 1.0)
        right = self.right["surprise"] * (self.right["confidence"] + 1.0)
        diff = abs(left - right)
        if diff < 0.05:
            return "balanced"
        elif left > right:
            return "left"
        else:
            return "right"

    def run_standalone(self, tick_interval=1.0):
        self.running = True
        print("ET cortical layer starting (standalone test)...")
        print("SOC threshold: 0.6  |  ! = approaching limit")
        print("Send signals: type a number between -1.0 and 1.0 and press Enter")
        print("Press Ctrl+C to stop.\n")

        import threading
        def input_loop():
            while self.running:
                try:
                    val = float(input())
                    self.input_event(val)
                    soc_l = " ** SOC FIRING **" if self.left["soc_firing"] else ""
                    soc_r = " ** SOC FIRING **" if self.right["soc_firing"] else ""
                    print(f"  Left SOC:{soc_l}  Right SOC:{soc_r}")
                except:
                    pass
        threading.Thread(target=input_loop, daemon=True).start()

        try:
            while self.running:
                self.tick()
                w = self.warning
                state = self.get_state()
                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"  [left loop]")
                print(f"    prediction: {self._bar(state['left']['prediction'])}")
                print(f"    surprise:   {self._bar(state['left']['surprise'], w['left_surprise'])}")
                print(f"    confidence: {self._bar(state['left']['confidence'])}")
                print(f"    soc_firing: {state['left']['soc_firing']}")
                print(f"  [right loop]")
                print(f"    prediction: {self._bar(state['right']['prediction'])}")
                print(f"    surprise:   {self._bar(state['right']['surprise'], w['right_surprise'])}")
                print(f"    confidence: {self._bar(state['right']['confidence'])}")
                print(f"    soc_firing: {state['right']['soc_firing']}")
                print(f"  [corpus callosum]")
                print(f"    bandwidth:  {self.cc_bandwidth:.3f}")
                print(f"    conflict:   {self._bar(state['cc']['conflict'], w['conflict'])}")
                print(f"  [integrated] {self.get_integrated_signal():+.3f}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nCortical layer stopped.")
            self.running = False

if __name__ == "__main__":
    et_cortical = CorticalLayer()
    et_cortical.run_standalone(tick_interval=1.0)
