import time
import threading
from datetime import datetime
from autonomic import AutonomicLayer
from limbic import LimbicLayer

class ETCore:
    def __init__(self):
        self.autonomic = AutonomicLayer()
        self.limbic = LimbicLayer()
        self.tick_count = 0
        self.running = False
        self.lock = threading.Lock()

    def _bar(self, value):
        pos = max(0, min(19, int((value + 1.0) * 10)))
        bar = list("-" * 20)
        bar[pos] = "|"
        return f"[{''.join(bar)}] {value:+.3f}"

    def tick(self):
        with self.lock:
            self.tick_count += 1

            # Autonomic ticks first — it's the foundation
            self.autonomic.tick()
            autonomic_state = self.autonomic.get_state()

            # Limbic receives autonomic state — arousal influences valence
            self.limbic.tick(autonomic_state=autonomic_state)
            limbic_state = self.limbic.get_state()

            return autonomic_state, limbic_state

    def interaction(self, valence_charge):
        # Someone is here — spike arousal and deliver valence charge
        with self.lock:
            # Arousal spikes on any interaction — curiosity before judgment
            self.autonomic.state["arousal"] = min(1.0,
                self.autonomic.state["arousal"] + 0.2
            )
            # Then valence charge arrives in limbic
            self.limbic.input_event(valence_charge)
        print(f"\n  >> Interaction received (valence: {valence_charge:+.2f})\n")

    def run(self, tick_interval=1.0):
        self.running = True
        print("ET core starting — autonomic + limbic loops active")
        print("Commands: [p] positive interaction  [n] negative  [q] quit\n")

        # Input thread so we can send interactions while it runs
        def input_loop():
            while self.running:
                try:
                    cmd = input()
                    if cmd == "p":
                        self.interaction(+0.4)
                    elif cmd == "n":
                        self.interaction(-0.4)
                    elif cmd == "q":
                        self.running = False
                except:
                    pass

        input_thread = threading.Thread(target=input_loop, daemon=True)
        input_thread.start()

        try:
            while self.running:
                autonomic_state, limbic_state = self.tick()

                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"  [autonomic]")
                print(f"    arousal:          {self._bar(autonomic_state['arousal'])}")
                print(f"    fatigue:          {self._bar(autonomic_state['fatigue'])}")
                print(f"    temperature:      {self._bar(autonomic_state['temperature'])}")
                print(f"  [limbic]")
                print(f"    valence:          {self._bar(limbic_state['valence'])}")
                print(f"    emotional_memory: {self._bar(limbic_state['emotional_memory'])}")
                print(f"    approach_avoid:   {self._bar(limbic_state['approach_avoid'])}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nET core stopped.")
            self.running = False

if __name__ == "__main__":
    et = ETCore()
    et.run(tick_interval=1.0)
