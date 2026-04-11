import random

class SleepSystem:
    """
    ET's sleep and consolidation system.
    
    When fatigue crosses threshold, ET enters sleep.
    During sleep:
    - Fatigue partially resets (rest)
    - Memory consolidation runs (low-valence episodes decay faster)
    - Word activations reorganize slightly
    - Arousal recovers toward baseline
    
    This makes sleep functional rather than just a failure state.
    Biologically accurate: REM sleep consolidates memory and
    clears metabolic waste. Deprivation causes cognitive decline.
    """

    def __init__(self):
        self.sleeping = False
        self.sleep_depth = 0.0
        self.sleep_ticks = 0
        self.total_sleep_ticks = 0
        self.cycles = 0

        self.sleep_threshold = 0.75     # fatigue level that triggers sleep
        self.wake_threshold = 0.3       # fatigue level that allows waking
        self.consolidation_rate = 0.002 # how fast memory clears during sleep

    def tick(self, autonomic, memory, word_store):
        fatigue = autonomic.state["fatigue"]

        if not self.sleeping:
            # Check if ET should fall asleep
            if fatigue >= self.sleep_threshold:
                self.sleeping = True
                self.sleep_depth = 0.0
                self.sleep_ticks = 0
                return "entering_sleep"
            return "awake"

        # ET is sleeping
        self.sleep_ticks += 1
        self.total_sleep_ticks += 1

        # Sleep deepens gradually
        self.sleep_depth = min(1.0, self.sleep_depth + 0.01)

        # Fatigue recovery during sleep — faster than drift rate
        # Must recover faster than fatigue accumulates or ET never wakes
        recovery = 0.008 * (0.5 + self.sleep_depth * 0.5)
        autonomic.state["fatigue"] = autonomic._clamp(
            autonomic.state["fatigue"] - recovery
        )

        # Arousal slowly recovers toward baseline during sleep
        arousal_recovery = 0.001
        autonomic.state["arousal"] = autonomic._clamp(
            autonomic.state["arousal"] + arousal_recovery
        )

        # Memory consolidation — low valence episodes decay faster during sleep
        # High valence episodes consolidate (activation boosted slightly)
        if self.sleep_ticks % 10 == 0:
            for ep in memory.episodes:
                if abs(ep["valence"]) < 0.2:
                    # Neutral memories clear during sleep
                    ep["activation"] -= self.consolidation_rate * 3
                elif abs(ep["valence"]) > 0.5:
                    # Significant memories consolidate
                    ep["activation"] = min(1.0,
                        ep["activation"] + self.consolidation_rate
                    )

            # Word store — rarely used words fade during sleep
            for word, data in word_store.words.items():
                if data["count"] <= 1:
                    data["activation"] -= self.consolidation_rate

        # Check if ET should wake up
        if fatigue <= self.wake_threshold:
            self.sleeping = False
            self.sleep_depth = 0.0
            self.cycles += 1
            # Full fatigue reset on wake — sleep actually helped
            autonomic.state["fatigue"] = max(0.0, self.wake_threshold - 0.1)
            # Arousal recovers toward a healthy baseline
            autonomic.state["arousal"] = autonomic._clamp(
                autonomic.state["arousal"] + 0.3
            )
            return "waking"

        return "sleeping"

    def get_state(self):
        return {
            "sleeping": self.sleeping,
            "sleep_depth": self.sleep_depth,
            "sleep_ticks": self.sleep_ticks,
            "total_sleep_ticks": self.total_sleep_ticks,
            "cycles": self.cycles,
        }
