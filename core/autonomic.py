import time
import os
from datetime import datetime

class AutonomicLayer:
    def __init__(self):
        self.state = {
            "arousal": 0.0,
            "fatigue": 0.0,
            "temperature": 0.0,
        }
        self.drift_rate = 0.002
        self.decay_rate = 0.001
        self.tick_count = 0
        self.running = False

    def _clamp(self, value):
        return max(-1.0, min(1.0, value))

    def _get_cpu_load(self):
        try:
            with open("/proc/stat") as f:
                fields = [float(x) for x in f.readline().split()[1:]]
            idle = fields[3]
            total = sum(fields)
            load = 1.0 - (idle / total)
            return self._clamp((load * 2.0) - 1.0)
        except:
            return 0.0

    def _bar(self, value):
        pos = int((value + 1.0) * 10)
        bar = list("-" * 20)
        pos = max(0, min(19, pos))
        bar[pos] = "|"
        return f"[{''.join(bar)}] {value:+.3f}"

    def tick(self):
        self.tick_count += 1

        self.state["fatigue"] = self._clamp(
            self.state["fatigue"] + self.drift_rate + (0.0 - self.state["fatigue"]) * self.decay_rate
        )

        cpu = self._get_cpu_load()
        self.state["temperature"] = self._clamp(
            self.state["temperature"] + (cpu - self.state["temperature"]) * 0.1
        )

        arousal_pull = (self.state["fatigue"] * 0.4) + (self.state["temperature"] * 0.6)
        self.state["arousal"] = self._clamp(
            self.state["arousal"] + (arousal_pull - self.state["arousal"]) * 0.05
        )

    def run(self, tick_interval=1.0):
        self.running = True
        print("ET autonomic layer starting...")
        print("Homeostasis target: 0.0  |  Range: -1.0 to +1.0")
        print("Press Ctrl+C to stop.\n")
        try:
            while self.running:
                self.tick()
                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"  arousal:     {self._bar(self.state['arousal'])}")
                print(f"  fatigue:     {self._bar(self.state['fatigue'])}")
                print(f"  temperature: {self._bar(self.state['temperature'])}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nAutonomic layer stopped.")
            self.running = False

if __name__ == "__main__":
    et = AutonomicLayer()
    et.run(tick_interval=1.0)
