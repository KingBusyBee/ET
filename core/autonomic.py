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
        self.warning = {
            "arousal": False,
            "fatigue": False,
            "temperature": False,
        }
        self.rebound = {
            "arousal": 0.0,
            "fatigue": 0.0,
            "temperature": 0.0,
        }
        self.drift_rate = 0.00008
        self.decay_rate = 0.001
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

    def _apply_resistance(self, signal, proposed_change):
        # As signal approaches ceiling/floor, resistance builds
        # At warning_threshold resistance starts
        # At 1.0 resistance is total
        abs_signal = abs(signal)
        if abs_signal >= self.warning_threshold:
            resistance = (abs_signal - self.warning_threshold) / (1.0 - self.warning_threshold)
            resistance = min(1.0, resistance)
            proposed_change = proposed_change * (1.0 - resistance)
        return proposed_change

    def _check_warning(self, signal_name):
        value = self.state[signal_name]
        was_warning = self.warning[signal_name]
        is_warning = abs(value) >= self.warning_threshold

        # Rebound triggers when warning clears after being active
        # Models adrenaline dump / second wind before deeper crash
        if was_warning and not is_warning:
            direction = -1.0 if value > 0 else 1.0
            # Brief spike opposite to direction of limit hit (second wind)
            # followed by overshoot past homeostasis (the crash)
            self.rebound[signal_name] = direction * self.rebound_factor
            # Arousal specifically gets a second wind boost before crash
            if signal_name == "arousal":
                self.state["arousal"] = self._clamp(
                    self.state["arousal"] + (-direction * self.rebound_factor * 0.5)
                )

        self.warning[signal_name] = is_warning
        return is_warning

    def _apply_rebound(self, signal_name):
        rebound = self.rebound[signal_name]
        if abs(rebound) > 0.001:
            self.state[signal_name] = self._clamp(
                self.state[signal_name] + rebound
            )
            self.rebound[signal_name] *= 0.5
        else:
            self.rebound[signal_name] = 0.0

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

    def tick(self):
        self.tick_count += 1

        # Fatigue
        fatigue_change = self.drift_rate + (0.0 - self.state["fatigue"]) * self.decay_rate
        fatigue_change = self._apply_resistance(self.state["fatigue"], fatigue_change)
        self.state["fatigue"] = self._clamp(self.state["fatigue"] + fatigue_change)
        self._apply_rebound("fatigue")
        self._check_warning("fatigue")

        # Temperature = metabolic activity, not CPU heat
        # Will be updated by et_core with real signal activity
        # Standalone mode uses a resting baseline
        cpu = self._get_cpu_load()
        temp_change = (cpu - self.state["temperature"]) * 0.1
        temp_change = self._apply_resistance(self.state["temperature"], temp_change)
        self.state["temperature"] = self._clamp(self.state["temperature"] + temp_change)
        self._apply_rebound("temperature")
        self._check_warning("temperature")

        # Arousal — pulled by fatigue and temperature
        arousal_pull = (self.state["fatigue"] * 0.4) + (self.state["temperature"] * 0.6)
        arousal_change = (arousal_pull - self.state["arousal"]) * 0.05
        arousal_change = self._apply_resistance(self.state["arousal"], arousal_change)
        self.state["arousal"] = self._clamp(self.state["arousal"] + arousal_change)
        self._apply_rebound("arousal")
        self._check_warning("arousal")

    def update_temperature(self, activity_level):
        # Called by et_core with real metabolic data
        target = activity_level
        change = (target - self.state["temperature"]) * 0.1
        change = self._apply_resistance(self.state["temperature"], change)
        self.state["temperature"] = self._clamp(self.state["temperature"] + change)

    def get_state(self):
        return dict(self.state)

    def get_warnings(self):
        return dict(self.warning)

    def get_corpus_callosum_bandwidth(self):
        # High arousal narrows bandwidth — stressed ET thinks in tunnels
        # Returns 0.0 (fully narrowed) to 1.0 (fully open)
        arousal = abs(self.state["arousal"])
        if arousal < self.warning_threshold:
            return 1.0
        narrowing = (arousal - self.warning_threshold) / (1.0 - self.warning_threshold)
        return max(0.0, 1.0 - narrowing)

    def run(self, tick_interval=1.0):
        self.running = True
        print("ET autonomic layer starting...")
        print("Homeostasis target: 0.0  |  Range: -1.0 to +1.0")
        print("Warning threshold: ±0.75  |  ! = approaching limit")
        print("Press Ctrl+C to stop.\n")
        try:
            while self.running:
                self.tick()
                w = self.warning
                print(f"Tick {self.tick_count:04d} | {datetime.now().strftime('%H:%M:%S')}")
                print(f"  arousal:     {self._bar(self.state['arousal'], w['arousal'])}")
                print(f"  fatigue:     {self._bar(self.state['fatigue'], w['fatigue'])}")
                print(f"  temperature: {self._bar(self.state['temperature'], w['temperature'])}")
                print(f"  cc_bandwidth:{self.get_corpus_callosum_bandwidth():.3f}")
                print()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            print("\nAutonomic layer stopped.")
            self.running = False

if __name__ == "__main__":
    et = AutonomicLayer()
    et.run(tick_interval=1.0)
