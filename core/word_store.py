import json
import os
from datetime import datetime

WORD_FILE = os.path.join(os.path.dirname(__file__), "../et_words.json")

class WordStore:
    """
    ET's emerging vocabulary.
    Words arrive with no meaning. Meaning accumulates through valence association.
    Words heard during high positive valence become positive words.
    Words heard during high negative valence become negative words.
    Words nobody uses decay and disappear.
    No dictionary. No rules. Just association.
    """
    def __init__(self):
        self.words = {}
        # Each word entry:
        # {
        #   "count": how many times heard,
        #   "valence_sum": accumulated valence when heard,
        #   "valence_avg": running average valence,
        #   "activation": current strength (decays),
        #   "first_heard": tick,
        #   "last_heard": tick,
        #   "positions": {"subject": n, "verb": n, "object": n, "qualifier": n}
        # }
        self.tick_count = 0
        self.decay_rate = 0.00005   # very slow — words persist
        self.load()

    def hear(self, text, valence, arousal, tick):
        """Process incoming text — extract words and associate with current signal state."""
        if not text:
            return

        # Clean and split
        import re
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

        for word in words:
            if word not in self.words:
                self.words[word] = {
                    "count": 0,
                    "valence_sum": 0.0,
                    "valence_avg": 0.0,
                    "activation": 0.5,
                    "first_heard": tick,
                    "last_heard": tick,
                    "positions": {"subject": 0, "verb": 0, "object": 0, "qualifier": 0}
                }

            w = self.words[word]
            w["count"] += 1
            w["valence_sum"] += valence
            w["valence_avg"] = w["valence_sum"] / w["count"]

            # High arousal at hearing = stronger encoding
            encoding_strength = 0.5 + abs(arousal) * 0.3 + abs(valence) * 0.2
            w["activation"] = min(1.0, w["activation"] + encoding_strength * 0.1)
            w["last_heard"] = tick

    def tick(self):
        """Decay all word activations. Prune dead words."""
        self.tick_count += 1
        to_remove = []
        for word, data in self.words.items():
            # High valence words decay slower
            rate = self.decay_rate * (1.0 - abs(data["valence_avg"]) * 0.5)
            data["activation"] -= rate
            if data["activation"] <= 0.0:
                to_remove.append(word)
        for word in to_remove:
            del self.words[word]

    def get_valence(self, word):
        """What emotional charge does ET associate with this word?"""
        w = self.words.get(word.lower())
        if not w:
            return 0.0
        return w["valence_avg"]

    def get_strongest(self, n=10):
        """Most activated words right now."""
        sorted_words = sorted(
            self.words.items(),
            key=lambda x: x[1]["activation"],
            reverse=True
        )
        return [(w, d["valence_avg"], d["activation"]) for w, d in sorted_words[:n]]

    def get_most_positive(self, n=5):
        """Words ET associates most positively."""
        sorted_words = sorted(
            self.words.items(),
            key=lambda x: x[1]["valence_avg"],
            reverse=True
        )
        return [(w, d["valence_avg"]) for w, d in sorted_words[:n] if d["count"] > 1]

    def get_most_negative(self, n=5):
        """Words ET associates most negatively."""
        sorted_words = sorted(
            self.words.items(),
            key=lambda x: x[1]["valence_avg"]
        )
        return [(w, d["valence_avg"]) for w, d in sorted_words[:n] if d["count"] > 1]

    def summary(self):
        if not self.words:
            return {"total_words": 0}
        return {
            "total_words": len(self.words),
            "most_positive": self.get_most_positive(3),
            "most_negative": self.get_most_negative(3),
            "strongest": [(w, round(a, 3)) for w, v, a in self.get_strongest(3)],
        }

    def save(self):
        data = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "word_count": len(self.words),
            "words": self.words
        }
        with open(WORD_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(WORD_FILE):
            print("No word store found. ET starting with no vocabulary.")
            return
        try:
            with open(WORD_FILE) as f:
                data = json.load(f)
            self.words = data.get("words", {})
            self.tick_count = data.get("tick_count", 0)
            print(f"Word store loaded: {len(self.words)} words known.")
        except Exception as e:
            print(f"Could not load word store: {e}")
