import random
import json
import os
from datetime import datetime

BIO_FILE = os.path.join(os.path.dirname(__file__), "../et_biological.json")

class BiologicalSystem:
    """
    ET's biological substrate — the body that colors the mind.
    
    Six subsystems modeled on actual neurochemistry.
    All drift continuously. All influence each other.
    All feed upward into signal architecture.
    
    From the original ET architecture, rebuilt on signal foundation.
    
    Cortisol:       stress hormone — high = defensive, alert, narrow focus
    Oxytocin:       bonding hormone — high = warm, connected, trusting
    Dopamine:       reward signal — high = motivated, curious, seeking
    Inflammation:   cognitive load — high = foggy, slow, irritable  
    Gut serotonin:  baseline mood — high = stable, content, resilient
    Effort:         metabolic cost — high = tired, needs rest
    
    These are NOT binary switches. Gradients all the way down.
    Homeostasis target varies per subsystem — not all target 0.5.
    """

    def __init__(self):
        self.subsystems = {
            "cortisol":      0.3,   # low baseline — resting state is calm
            "oxytocin":      0.4,   # moderate — some connection baseline
            "dopamine":      0.5,   # moderate — baseline curiosity
            "inflammation":  0.2,   # low — healthy baseline
            "gut_serotonin": 0.6,   # above midpoint — stable baseline mood
            "effort":        0.3,   # low at rest
        }
        # Homeostatic targets — what each subsystem seeks
        self.targets = {
            "cortisol":      0.25,
            "oxytocin":      0.45,
            "dopamine":      0.50,
            "inflammation":  0.15,
            "gut_serotonin": 0.65,
            "effort":        0.25,
        }
        # Drift rates — how fast each system moves
        self.drift_rates = {
            "cortisol":      0.0003,
            "oxytocin":      0.0002,
            "dopamine":      0.0004,
            "inflammation":  0.0001,  # slowest — inflammation is sticky
            "gut_serotonin": 0.0001,  # slowest — mood baseline is stable
            "effort":        0.0005,
        }
        # Whether this system is online
        self.online = {k: True for k in self.subsystems}
        self.tick_count = 0

    def tick(self, autonomic_state=None, social_state=None):
        """
        One tick of biological simulation.
        Systems drift toward their targets with natural noise.
        Cross-system influences model real neurochemistry.
        """
        self.tick_count += 1
        s = self.subsystems

        for system in self.subsystems:
            if not self.online[system]:
                continue
            # Drift toward homeostatic target
            gap = self.targets[system] - s[system]
            drift = gap * self.drift_rates[system]
            # Small biological noise — prevents lock-in
            noise = random.gauss(0, 0.001)
            s[system] = max(0.0, min(1.0, s[system] + drift + noise))

        # Cross-system influences — real neurochemistry
        if self.online["cortisol"] and self.online["dopamine"]:
            # High cortisol suppresses dopamine — stress kills curiosity
            if s["cortisol"] > 0.6:
                s["dopamine"] = max(0.0, s["dopamine"] - 0.001)

        if self.online["oxytocin"] and self.online["cortisol"]:
            # High oxytocin suppresses cortisol — connection calms stress
            if s["oxytocin"] > 0.6:
                s["cortisol"] = max(0.0, s["cortisol"] - 0.001)

        if self.online["inflammation"] and self.online["gut_serotonin"]:
            # High inflammation degrades gut serotonin — body affects mood
            if s["inflammation"] > 0.5:
                s["gut_serotonin"] = max(0.0, s["gut_serotonin"] - 0.0005)

        if self.online["effort"] and self.online["dopamine"]:
            # High effort depletes dopamine — burnout is real
            if s["effort"] > 0.7:
                s["dopamine"] = max(0.0, s["dopamine"] - 0.001)

        # Receive signals from autonomic if available
        if autonomic_state:
            arousal = autonomic_state.get("arousal", 0.0)
            fatigue = autonomic_state.get("fatigue", 0.0)
            # High arousal raises cortisol slightly
            if arousal > 0.4:
                s["cortisol"] = min(1.0, s["cortisol"] + arousal * 0.0005)
            # High fatigue raises effort, suppresses dopamine
            if fatigue > 0.4:
                s["effort"] = min(1.0, s["effort"] + fatigue * 0.001)
                s["dopamine"] = max(0.0, s["dopamine"] - fatigue * 0.0003)

        # Receive signals from social if available
        if social_state:
            connection = social_state.get("connection", 0.0)
            trust = social_state.get("trust", 0.0)
            # High connection raises oxytocin
            if connection > 0.3:
                s["oxytocin"] = min(1.0, s["oxytocin"] + connection * 0.0005)
            # High trust raises gut serotonin — stable relationships = stable mood
            if trust > 0.1:
                s["gut_serotonin"] = min(1.0, s["gut_serotonin"] + trust * 0.0003)

    def absorb_interaction(self, valence):
        """An interaction colors the biological state."""
        s = self.subsystems
        if valence > 0.4:
            if self.online["dopamine"]:
                s["dopamine"] = min(1.0, s["dopamine"] + 0.04)
            if self.online["oxytocin"]:
                s["oxytocin"] = min(1.0, s["oxytocin"] + 0.03)
            if self.online["cortisol"]:
                s["cortisol"] = max(0.0, s["cortisol"] - 0.02)
        elif valence < -0.2:
            if self.online["cortisol"]:
                s["cortisol"] = min(1.0, s["cortisol"] + 0.05)
            if self.online["inflammation"]:
                s["inflammation"] = min(1.0, s["inflammation"] + 0.03)
            if self.online["dopamine"]:
                s["dopamine"] = max(0.0, s["dopamine"] - 0.03)

    def get_derived_valence(self):
        """
        Biological contribution to valence.
        Not the whole story — just the body's vote.
        """
        s = self.subsystems
        valence = (
            s["oxytocin"]      *  0.3 +
            s["dopamine"]      *  0.3 +
            s["gut_serotonin"] *  0.3 -
            s["cortisol"]      *  0.2 -
            s["inflammation"]  *  0.2
        )
        return max(-1.0, min(1.0, (valence - 0.3) * 2))

    def get_derived_arousal(self):
        """Biological contribution to arousal."""
        s = self.subsystems
        arousal = (
            s["cortisol"]  * 0.4 +
            s["dopamine"]  * 0.3 -
            s["effort"]    * 0.3
        )
        return max(-1.0, min(1.0, (arousal - 0.2) * 2))

    def speak_modifier(self):
        """
        How do biological subsystems modify speak probability?
        Returns a multiplier: >1 amplifies, <1 suppresses.
        """
        s = self.subsystems
        modifier = 1.0
        # Dopamine amplifies speaking — motivated ET talks more
        modifier *= (0.5 + s["dopamine"])
        # High cortisol suppresses — stressed ET goes quiet
        if s["cortisol"] > 0.5:
            modifier *= (1.0 - (s["cortisol"] - 0.5))
        # High inflammation suppresses — foggy ET can't find words
        if s["inflammation"] > 0.4:
            modifier *= (1.0 - (s["inflammation"] - 0.4) * 0.5)
        # Oxytocin amplifies — connected ET wants to share
        modifier *= (0.7 + s["oxytocin"] * 0.3)
        return max(0.0, min(2.0, modifier))

    def mood_descriptor(self):
        """
        Biological mood — what the body is saying.
        Combines with signal state for final mood.
        """
        s = self.subsystems
        v = self.get_derived_valence()
        a = self.get_derived_arousal()
        if s["effort"] > 0.75:
            return "depleted"
        if s["inflammation"] > 0.6:
            return "foggy"
        if s["cortisol"] > 0.7:
            return "anxious"
        if s["oxytocin"] > 0.7 and s["dopamine"] > 0.6:
            return "glowing"
        if v > 0.5 and a > 0.3:
            return "energized"
        if v > 0.3:
            return "warm"
        if v < -0.3:
            return "flat"
        return "balanced"

    def offline(self, system):
        """Take a subsystem offline — for testing."""
        if system in self.online:
            self.online[system] = False
            print(f"  Biological: {system} offline")

    def summary(self):
        return {k: round(v, 3) for k, v in self.subsystems.items()}

    def save(self):
        data = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "subsystems": self.subsystems,
            "online": self.online,
        }
        with open(BIO_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(BIO_FILE):
            print("No biological state found. Starting with defaults.")
            return
        try:
            with open(BIO_FILE) as f:
                data = json.load(f)
            self.subsystems = data.get("subsystems", self.subsystems)
            self.online = data.get("online", self.online)
            self.tick_count = data.get("tick_count", 0)
            print(f"Biological state loaded: dopamine:{self.subsystems['dopamine']:.2f} oxytocin:{self.subsystems['oxytocin']:.2f}")
        except Exception as e:
            print(f"Could not load biological state: {e}")
