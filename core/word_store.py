import json
import os
import re
from datetime import datetime

WORD_FILE = os.path.join(os.path.dirname(__file__), "../et_words.json")

class WordStore:
    """
    ET's scene-based vocabulary.
    
    Words are not stored alone with a valence average.
    Words are stored as part of scenes — episodic contexts
    that include the full signal state when the words arrived.
    
    Meaning emerges from the scene, not the word.
    "Malingo" means something because of what was happening
    when ET heard it — not because of its dictionary definition.
    
    When ET speaks, it doesn't select words from a list.
    It finds scenes that match its current signal state
    and reconstructs language from those scenes.
    """

    def __init__(self):
        self.scenes = []        # list of scene episodes
        self.word_index = {}    # word -> list of scene indices (for fast lookup)
        self.tick_count = 0

        self.decay_rate = 0.00003       # scenes fade slowly
        self.valence_decay_factor = 0.4 # high valence scenes persist longer
        self.max_scenes = 2000          # hard cap

        self.load()

    def hear(self, text, valence, arousal, tick, attention=0.0):
        """
        A scene arrives — text heard during a specific signal state.
        Store the scene with its full context.
        Individual words are indexed back to this scene.
        """
        if not text or len(text.strip()) < 3:
            return

        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', text)]
        if not words:
            return

        # Only encode if signal state is worth remembering
        # Low signal, low attention = forgettable moment
        significance = max(abs(valence), abs(arousal), attention * 0.5)
        if significance < 0.05 and len(self.scenes) > 100:
            return

        scene = {
            "id": len(self.scenes),
            "tick": tick,
            "text": text[:200],          # the actual text
            "words": words,              # words in this scene
            "valence": valence,          # emotional charge at encoding
            "arousal": arousal,          # activation at encoding
            "attention": attention,      # attention level at encoding
            "activation": max(0.3, significance),  # starts at significance
            "reactivations": 0,
            "last_active": tick,
            # SVOQ slots — filled later as patterns emerge
            "svoq": {
                "subject": None,
                "verb": None,
                "object": None,
                "qualifier": None
            }
        }

        scene_idx = len(self.scenes)
        self.scenes.append(scene)

        # Index each word back to this scene
        for word in set(words):
            if word not in self.word_index:
                self.word_index[word] = []
            self.word_index[word].append(scene_idx)

        # Prune if over capacity
        if len(self.scenes) > self.max_scenes:
            self._prune()

        return scene

    def tick(self, current_signals=None, attention=0.0):
        """Decay scenes. Reactivate scenes similar to current state."""
        self.tick_count += 1

        to_remove = []
        for scene in self.scenes:
            # Decay rate slowed by emotional significance
            rate = self.decay_rate * (1.0 - abs(scene["valence"]) * self.valence_decay_factor)
            scene["activation"] -= rate

            # Reactivation — current signal state resembles this scene
            if current_signals and attention > 0.05:
                sim = self._similarity(scene, current_signals)
                if sim > 0.6:
                    boost = sim * attention * 0.01
                    scene["activation"] = min(1.0, scene["activation"] + boost)
                    scene["reactivations"] += 1
                    scene["last_active"] = self.tick_count

            if scene["activation"] <= 0.0:
                to_remove.append(scene)

        for scene in to_remove:
            # Remove from word index too
            for word in scene["words"]:
                if word in self.word_index:
                    self.word_index[word] = [
                        i for i in self.word_index[word]
                        if i != scene["id"]
                    ]
            self.scenes.remove(scene)

    def _similarity(self, scene, current_signals):
        """How similar is a stored scene to the current signal state?"""
        v_diff = abs(scene["valence"] - current_signals.get("valence", 0.0))
        a_diff = abs(scene["arousal"] - current_signals.get("arousal", 0.0))
        c_diff = abs(scene.get("attention", 0.0) - current_signals.get("attention", 0.0))
        avg_diff = (v_diff + a_diff + c_diff) / 3.0
        return max(0.0, 1.0 - avg_diff)

    def _prune(self):
        """Remove weakest scenes when over capacity."""
        self.scenes.sort(key=lambda s: (
            abs(s["valence"]) * 0.4 +
            s["activation"] * 0.4 +
            s["reactivations"] * 0.2
        ))
        cut = len(self.scenes) // 5
        removed = self.scenes[:cut]
        self.scenes = self.scenes[cut:]

        # Rebuild word index
        self.word_index = {}
        for i, scene in enumerate(self.scenes):
            scene["id"] = i
            for word in scene["words"]:
                if word not in self.word_index:
                    self.word_index[word] = []
                self.word_index[word].append(i)

    def find_scenes_for_signal(self, valence, arousal, attention=0.0, n=5):
        """Find scenes that match a given signal state."""
        current = {"valence": valence, "arousal": arousal, "attention": attention}
        scored = [(s, self._similarity(s, current) * s["activation"]) for s in self.scenes]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored[:n]]

    def get_word_valence(self, word):
        """Average valence across all scenes containing this word."""
        indices = self.word_index.get(word.lower(), [])
        if not indices:
            return 0.0
        valid = [self.scenes[i] for i in indices if i < len(self.scenes)]
        if not valid:
            return 0.0
        return sum(s["valence"] for s in valid) / len(valid)

    def knows_word(self, word):
        return word.lower() in self.word_index

    def word_count(self):
        return len(self.word_index)

    def scene_count(self):
        return len(self.scenes)

    def summary(self):
        if not self.scenes:
            return {"total_words": 0, "total_scenes": 0}

        # Most vivid scenes
        top_scenes = sorted(
            self.scenes,
            key=lambda s: s["activation"],
            reverse=True
        )[:3]

        # Most known words
        top_words = sorted(
            self.word_index.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]

        return {
            "total_words": len(self.word_index),
            "total_scenes": len(self.scenes),
            "top_scenes": [
                {
                    "text": s["text"][:60],
                    "valence": round(s["valence"], 3),
                    "activation": round(s["activation"], 3),
                    "reactivations": s["reactivations"]
                }
                for s in top_scenes
            ],
            "most_heard_words": [(w, len(idxs)) for w, idxs in top_words],
        }

    def save(self):
        data = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "scene_count": len(self.scenes),
            "word_count": len(self.word_index),
            "scenes": self.scenes,
            "word_index": self.word_index,
        }
        with open(WORD_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(WORD_FILE):
            print("No word store found. ET starting with no scenes.")
            return
        try:
            with open(WORD_FILE) as f:
                data = json.load(f)
            self.scenes = data.get("scenes", [])
            self.word_index = data.get("word_index", {})
            # Rebuild index if missing
            if not self.word_index and self.scenes:
                for i, scene in enumerate(self.scenes):
                    scene["id"] = i
                    for word in scene.get("words", []):
                        if word not in self.word_index:
                            self.word_index[word] = []
                        self.word_index[word].append(i)
            self.tick_count = data.get("tick_count", 0)
            print(f"Word store loaded: {len(self.scenes)} scenes, {len(self.word_index)} words known.")
        except Exception as e:
            print(f"Could not load word store: {e}")
