import json
import os
import time
from datetime import datetime
from collections import deque

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "../et_memory.json")

class MemorySystem:
    def __init__(self):
        self.episodes = []          # list of memory episodes
        self.max_episodes = 1000    # hard cap before aggressive pruning
        self.tick_count = 0

        # Decay rates
        self.base_decay = 0.0001       # per tick — slow fade
        self.valence_decay_factor = 0.3  # high valence decays slower
        self.attention_boost = 0.05    # reactivation boost

        # Encoding threshold — only encode significant moments
        self.encoding_threshold = 0.15  # minimum surprise or valence to encode

        self.load()

    def _valence_weight(self, valence):
        # High absolute valence = slower decay
        # Trauma and joy both resist forgetting
        return 1.0 - (abs(valence) * self.valence_decay_factor)

    def encode(self, signal_state, surprise, valence, attention, context=None):
        # Only encode significant moments
        significance = max(abs(surprise), abs(valence), attention)
        if significance < self.encoding_threshold:
            return None

        episode = {
            "id": len(self.episodes),
            "tick": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "activation": significance,      # starts at significance level
            "valence": valence,              # emotional charge at encoding
            "surprise": surprise,            # how unexpected this was
            "attention": attention,          # how much attention was paid
            "signal_snapshot": {             # signal state at this moment
                "arousal": signal_state.get("arousal", 0.0),
                "fatigue": signal_state.get("fatigue", 0.0),
                "connection": signal_state.get("connection", 0.0),
                "protest": signal_state.get("protest", 0.0),
                "valence": signal_state.get("valence", 0.0),
                "emotional_memory": signal_state.get("emotional_memory", 0.0),
            },
            "context": context or {},        # any extra context (text, etc)
            "reactivation_count": 0,         # how many times recalled
            "last_activation_tick": self.tick_count,
        }

        self.episodes.append(episode)

        # Prune if over capacity
        if len(self.episodes) > self.max_episodes:
            self._prune()

        return episode

    def tick(self, current_signals, attention):
        self.tick_count += 1

        # Decay all memories
        to_remove = []
        for ep in self.episodes:
            decay_rate = self.base_decay * self._valence_weight(ep["valence"])
            ep["activation"] -= decay_rate

            # Check for reactivation — does current state resemble this memory?
            similarity = self._similarity(ep["signal_snapshot"], current_signals)
            if similarity > 0.7 and attention > 0.1:
                # Reactivation — attention is on something similar
                boost = self.attention_boost * similarity * attention
                ep["activation"] = min(1.0, ep["activation"] + boost)
                ep["reactivation_count"] += 1
                ep["last_activation_tick"] = self.tick_count

            # Mark for removal if faded completely
            if ep["activation"] <= 0.0:
                to_remove.append(ep)

        for ep in to_remove:
            self.episodes.remove(ep)

    def _similarity(self, snapshot, current):
        # How similar is a stored signal state to the current one?
        # Simple distance measure across key signals
        keys = ["arousal", "valence", "connection", "protest"]
        total = 0.0
        count = 0
        for k in keys:
            if k in snapshot and k in current:
                diff = abs(snapshot[k] - current.get(k, 0.0))
                total += 1.0 - min(1.0, diff)
                count += 1
        return total / count if count > 0 else 0.0

    def _prune(self):
        # Remove weakest memories when over capacity
        # Keep high valence and recently reactivated
        self.episodes.sort(key=lambda e: (
            abs(e["valence"]) * 0.5 +
            e["activation"] * 0.3 +
            e["reactivation_count"] * 0.2
        ))
        # Remove bottom 20%
        cut = len(self.episodes) // 5
        self.episodes = self.episodes[cut:]

    def get_strongest(self, n=5):
        # Return n most activated memories
        sorted_eps = sorted(
            self.episodes,
            key=lambda e: e["activation"],
            reverse=True
        )
        return sorted_eps[:n]

    def get_most_reactivated(self, n=5):
        # Return n most frequently recalled memories
        sorted_eps = sorted(
            self.episodes,
            key=lambda e: e["reactivation_count"],
            reverse=True
        )
        return sorted_eps[:n]

    def summary(self):
        if not self.episodes:
            return "No memories yet."
        avg_activation = sum(e["activation"] for e in self.episodes) / len(self.episodes)
        avg_valence = sum(e["valence"] for e in self.episodes) / len(self.episodes)
        most_reactivated = max(self.episodes, key=lambda e: e["reactivation_count"])
        return {
            "total_episodes": len(self.episodes),
            "avg_activation": round(avg_activation, 4),
            "avg_valence": round(avg_valence, 4),
            "most_reactivated_tick": most_reactivated["tick"],
            "most_reactivated_count": most_reactivated["reactivation_count"],
        }

    def save(self):
        data = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "episode_count": len(self.episodes),
            "episodes": self.episodes
        }
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(MEMORY_FILE):
            print("No memory file found. ET starting with no memories.")
            return
        try:
            with open(MEMORY_FILE) as f:
                data = json.load(f)
            self.tick_count = data.get("tick_count", 0)
            self.episodes = data.get("episodes", [])
            print(f"Memory loaded: {len(self.episodes)} episodes remembered.")
        except Exception as e:
            print(f"Could not load memory: {e}. Starting fresh.")
