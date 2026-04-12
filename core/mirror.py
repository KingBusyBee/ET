import json
import os
import re
from collections import deque
from datetime import datetime

MIRROR_FILE = os.path.join(os.path.dirname(__file__), "../et_mirror.json")

class MirrorSystem:
    """
    ET's mirror neuron analog.
    
    Tracks statistical patterns in the primary caregiver's language.
    Not copying — resonating. ET develops stylistic affinity with
    the person it talks to most, the way children sound like their parents.
    
    Tracks:
    - Average message length (words)
    - Question frequency (how often you ask vs state)
    - Sentence rhythm (short/punchy vs long/flowing)
    - Vocabulary diversity (how many unique words per message)
    - Energy level (exclamations, capitalization patterns)
    
    Applied loosely in output construction —
    ET's signal state still drives content.
    Style is just the shape the content takes.
    
    Minimum 25 samples before mirror activates —
    avoids cold start mimicry.
    """

    MIN_SAMPLES = 25
    MAX_HISTORY = 200
    ADAPTATION_RATE = 0.05  # slow drift — not instant copying

    def __init__(self):
        self.samples = deque(maxlen=self.MAX_HISTORY)
        self.profile = {
            "avg_length":      4.0,   # words per message
            "question_rate":   0.2,   # fraction that are questions
            "exclaim_rate":    0.1,   # fraction with exclamation
            "vocab_diversity": 0.6,   # unique/total word ratio
            "rhythm":          "medium",  # short/medium/long
        }
        self.active = False
        self.sample_count = 0
        self.load()

    def observe(self, text):
        """
        Observe a user message and update style profile.
        Called every time the user types something.
        """
        if not text or len(text.strip()) < 2:
            return

        words = re.findall(r"[a-zA-Z']+", text.lower())
        if not words:
            return

        sample = {
            "length":    len(words),
            "is_question": text.strip().endswith("?"),
            "is_exclaim":  text.strip().endswith("!"),
            "unique_ratio": len(set(words)) / len(words) if words else 0,
            "text":      text[:100],
        }
        self.samples.append(sample)
        self.sample_count += 1

        # Activate after minimum samples
        if self.sample_count >= self.MIN_SAMPLES:
            self.active = True
            self._update_profile()

    def _update_profile(self):
        """Slowly update profile from recent samples."""
        if len(self.samples) < self.MIN_SAMPLES:
            return

        recent = list(self.samples)[-50:]  # use last 50 samples

        avg_len = sum(s["length"] for s in recent) / len(recent)
        q_rate = sum(1 for s in recent if s["is_question"]) / len(recent)
        e_rate = sum(1 for s in recent if s["is_exclaim"]) / len(recent)
        div = sum(s["unique_ratio"] for s in recent) / len(recent)

        # Slow drift toward observed patterns
        r = self.ADAPTATION_RATE
        p = self.profile
        p["avg_length"]      += (avg_len - p["avg_length"]) * r
        p["question_rate"]   += (q_rate  - p["question_rate"]) * r
        p["exclaim_rate"]    += (e_rate  - p["exclaim_rate"]) * r
        p["vocab_diversity"] += (div     - p["vocab_diversity"]) * r

        # Rhythm classification
        if p["avg_length"] < 5:
            p["rhythm"] = "short"
        elif p["avg_length"] < 12:
            p["rhythm"] = "medium"
        else:
            p["rhythm"] = "long"

    def get_complexity_target(self, base_complexity):
        """
        Suggest output complexity based on user's style.
        ET mirrors length loosely — not exactly.
        Only active after MIN_SAMPLES.
        """
        if not self.active:
            return base_complexity

        rhythm = self.profile["rhythm"]
        if rhythm == "short":
            # User speaks briefly — ET stays concise
            return max(1, min(base_complexity, 2))
        elif rhythm == "long":
            # User elaborates — ET can extend
            return min(4, base_complexity + 1)
        return base_complexity

    def get_learning_boost(self):
        """
        How much to boost learning from user input vs story input.
        Capped at 4x — strong but not drowning.
        Builds gradually as sample count grows.
        """
        if self.sample_count < 5:
            return 1.5  # slight boost even early
        if self.sample_count < 25:
            return 2.5
        return 4.0  # full boost after profile is established

    def summary(self):
        return {
            "active": self.active,
            "samples": self.sample_count,
            "profile": {k: round(v, 3) if isinstance(v, float) else v
                       for k, v in self.profile.items()},
        }

    def save(self):
        data = {
            "timestamp": datetime.now().isoformat(),
            "sample_count": self.sample_count,
            "profile": self.profile,
            "samples": list(self.samples),
        }
        with open(MIRROR_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(MIRROR_FILE):
            return
        try:
            with open(MIRROR_FILE) as f:
                data = json.load(f)
            self.sample_count = data.get("sample_count", 0)
            self.profile = data.get("profile", self.profile)
            samples = data.get("samples", [])
            self.samples = deque(samples, maxlen=self.MAX_HISTORY)
            self.active = self.sample_count >= self.MIN_SAMPLES
            if self.active:
                print(f"Mirror system loaded: {self.sample_count} samples, "
                      f"rhythm:{self.profile['rhythm']}")
        except Exception as e:
            print(f"Could not load mirror system: {e}")
