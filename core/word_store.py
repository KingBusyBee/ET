import json
import os
from datetime import datetime

SCENE_FILE = os.path.join(os.path.dirname(__file__), "../et_scenes.json")

class WordStore:
    """
    ET signal scene memory.
    
    Stores moments — not words.
    Each scene is a snapshot of ET signal state during an experience.
    Text is saved as context annotation only, not analyzed.
    
    Vocabulary will emerge later from patterns across scenes.
    For now: experience first, language later.
    """

    def __init__(self):
        self.scenes = []
        self.tick_count = 0
        self.decay_rate = 0.00003
        self.valence_decay_factor = 0.4
        self.max_scenes = 3000
        self.load()

    def hear(self, text, valence, arousal, tick, attention=0.0):
        significance = max(abs(valence), abs(arousal) * 0.5, attention * 0.3)
        if significance < 0.05 and len(self.scenes) > 50:
            return None

        scene = {
            "id": len(self.scenes),
            "tick": tick,
            "context": text[:150] if text else "",
            "valence": valence,
            "arousal": arousal,
            "attention": attention,
            "activation": max(0.2, significance),
            "reactivations": 0,
            "last_active": tick,
        }
        self.scenes.append(scene)

        if len(self.scenes) > self.max_scenes:
            self._prune()

        return scene

    def tick(self, current_signals=None, attention=0.0):
        self.tick_count += 1
        to_remove = []

        for scene in self.scenes:
            rate = self.decay_rate * (1.0 - abs(scene["valence"]) * self.valence_decay_factor)
            scene["activation"] -= rate

            if current_signals and attention > 0.05:
                sim = self._similarity(scene, current_signals)
                if sim > 0.6:
                    scene["activation"] = min(1.0, scene["activation"] + sim * attention * 0.01)
                    scene["reactivations"] += 1
                    scene["last_active"] = self.tick_count

            if scene["activation"] <= 0.0:
                to_remove.append(scene)

        for scene in to_remove:
            self.scenes.remove(scene)

    def _similarity(self, scene, current):
        v = abs(scene["valence"] - current.get("valence", 0.0))
        a = abs(scene["arousal"] - current.get("arousal", 0.0))
        return max(0.0, 1.0 - (v + a) / 2.0)

    def find_scenes_for_signal(self, valence, arousal, attention=0.0, n=5):
        current = {"valence": valence, "arousal": arousal}
        scored = [(s, self._similarity(s, current) * s["activation"]) for s in self.scenes]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored[:n]]

    def _prune(self):
        self.scenes.sort(key=lambda s: abs(s["valence"]) * 0.5 + s["activation"] * 0.5)
        self.scenes = self.scenes[len(self.scenes) // 5:]
        for i, s in enumerate(self.scenes):
            s["id"] = i

    def scene_count(self):
        return len(self.scenes)

    def word_count(self):
        return 0  # no word tracking — vocabulary comes later

    def knows_word(self, word):
        return False  # not tracking words yet

    def get_word_valence(self, word):
        return 0.0  # not tracking words yet

    def summary(self):
        if not self.scenes:
            return {"total_scenes": 0, "total_words": 0}
        top = sorted(self.scenes, key=lambda s: s["activation"], reverse=True)[:3]
        return {
            "total_scenes": len(self.scenes),
            "total_words": 0,
            "top_scenes": [
                {"context": s["context"][:60], "valence": round(s["valence"], 3),
                 "activation": round(s["activation"], 3), "reactivations": s["reactivations"]}
                for s in top
            ]
        }

    def save(self):
        data = {
            "tick_count": self.tick_count,
            "timestamp": datetime.now().isoformat(),
            "scene_count": len(self.scenes),
            "scenes": self.scenes
        }
        path = SCENE_FILE
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        # Try new scene file first, fall back to old word file
        paths = [SCENE_FILE,
                 os.path.join(os.path.dirname(__file__), "../et_words.json")]
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    self.scenes = data.get("scenes", [])
                    self.tick_count = data.get("tick_count", 0)
                    # Strip word-specific fields if migrating from old format
                    for s in self.scenes:
                        s.pop("words", None)
                        s.pop("svoq", None)
                    print(f"Scene memory loaded: {len(self.scenes)} scenes.")
                    return
                except Exception as e:
                    print(f"Could not load scenes: {e}")
        print("No scene memory found. ET starting fresh.")
