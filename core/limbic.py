import time
import os
from datetime import datetime

class LimbicLayer:
    def __init__(self):
        self.state = {
            "valence": 0.0,       # positive/negative charge on current experience
            "emotional_memory": 0.0,  # accumulated valence history — slow moving
            "approach_avoid": 0.0,    # behavioral tendency emerging from valence
        }
        self.drift_rate = 0.001       # slower than autonomic — emotions linger
        self.memory_rate = 0.0005     # emotional memory is very slow to change
        self.tick_count = 0
        self.running = False

    def _clamp(self, value):
        return max(-1.0, min(1.0, value))

    def _bar(self, value):
        pos = max(0, min(19, int((value + 1.0) * 10)))
        bar = list("-" * 20)
        bar[pos] = "|"
        return f"[{''.join(bar)}] {value:+.3f}"

    def receive_autonomic(self, autonomic_state):
        # High arousal amplifies valence response
        # Low arousal dampens it — drowsy ET feels less
        arousal = autonomic_state.get("arousal", 0.0)
        self.arousal_influence = arousal

    def input_event(self, valence_charge):
        # External interaction — someone is there
        # valence_charge: +1.0 = very positive, -1.0 = very negative
        # Arousal amplifies how strongly this lands
        amplified = valence_charge * (1.0 + abs(self.arousal_influence) * 0.5)
        self.state["valence"] = self._clamp(
            self.state["valence"] + amplified * 0.3
        )

    def tick(self, autonomic_state=None):
        self.tick_count += 1

        if autonomic_state:
            self.receive_autonomic(autonomic_state)

        # Valence drifts back toward emotional memory, not zero
        # This means past experience shapes what "neutral" feels like
        gap_to_memory = self.state["emotional_memory"] - self.state["valence"]
        self.state["valence"] = self._clamp(
            self.state["valence"] + gap_to_memory * self.drift_rate * 10
        )

        # Emotional memory accumulates very slowly from valence
        gap_to_valence = self.state["valence"] - self.state["emotional_memory"]
        self.state["emotional_memory"] = self._clamp(
            self.state["emotional_memory"] + gap_to_valence * self.memory_rate
        )

        # Approach/avoid emerges from combined valence and emotional memory
        # Positive = approach, negative = avoid
        combined = (self.state["valence"] * 0.7) + (self.state["emotional_memory"] * 0.3)
        self.state["approach_avoid"] = self._clamp(
            self.state["approach_avoid"] + (combined - self.state["approach_avoid"]) * 0.05
        )

    def get_state(self):
        return dict(self.state)

    def run_standalone(self, tick_interval=1.0):
        self.running = True
        print("ET limbic layer starting (standalone test)...")
        print("Homeostasis target: 0.0  |  Range: -1.0 to +1.0")
        print("Press Ctrl+C to stop.\n")
        try:
            while self.running:
                self.tick()
                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"  valence:          {self._bar(self.state['valence'])}")
                print(f"  emotional_memory: {self._bar(self.state['emotional_memory'])}")
                print(f"  approach_avoid:   {self._bar(self.state['approach_avoid'])}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nLimbic layer stopped.")
            self.running = False

if __name__ == "__main__":
    et_limbic = LimbicLayer()
    et_limbic.run_standalone(tick_interval=1.0)
