import json
import os
import re
import random
from collections import defaultdict, Counter
from datetime import datetime

COOC_FILE = os.path.join(os.path.dirname(__file__), "../et_cooccurrence.json")

class CoOccurrenceNetwork:
    """
    ET's subconscious language layer.
    Words that appear near each other build connections.
    Words that appear during high valence moments get positive charge.
    The drive to speak emerges from accumulated network activation.
    Not an LLM — meaning built from signal-weighted experience.
    """

    def __init__(self, window=4, learning_rate=0.06, decay=0.9999):
        self.weights = defaultdict(lambda: defaultdict(float))
        self.word_valence = {}
        self.word_freq = Counter()
        self.window = window
        self.lr = learning_rate
        self.decay_rate = decay
        self.total_updates = 0

        # Speak pressure and probability
        self.speak_pressure = 0.0
        self.pressure_decay = 0.995
        self.speak_base_prob = 0.0005
        self.speak_max_prob = 0.85
        self.speak_experience = 0.0

    def learn(self, text, valence, arousal, attention=0.0):
        tokens = [t.lower() for t in re.findall(r"[a-zA-Z']+", text) if len(t) > 1]
        if not tokens:
            return

        # Track recency — last 50 words heard
        if not hasattr(self, "recent_words"):
            self.recent_words = []
        self.recent_words.extend(tokens)
        self.recent_words = self.recent_words[-100:]

        boost = 1.0 + abs(valence) * 0.5 + attention * 0.3

        for i, word in enumerate(tokens):
            self.word_freq[word] += 1

            if word not in self.word_valence:
                self.word_valence[word] = valence * 0.5
            else:
                self.word_valence[word] += (valence - self.word_valence[word]) * 0.05

            start = max(0, i - self.window)
            end = min(len(tokens), i + self.window + 1)
            context = tokens[start:end]

            for other in context:
                if other == word:
                    continue
                self.weights[word][other] += self.lr * boost
                self.weights[other][word] += self.lr * boost

                if word in self.word_valence and other in self.word_valence:
                    diff = self.word_valence[word] - self.word_valence[other]
                    self.word_valence[other] += diff * 0.03
                    self.word_valence[other] = max(-1.0, min(1.0, self.word_valence[other]))

        self.total_updates += 1
        self.speak_experience += len(set(tokens)) * 0.1

        activation = min(1.0, len(set(tokens)) * 0.05 * boost)
        self.speak_pressure = min(5.0, self.speak_pressure + activation * 0.1)

    def tick(self):
        self.speak_pressure *= self.pressure_decay
        if self.total_updates > 0 and self.total_updates % 1000 == 0:
            self._decay_weights()

    def _decay_weights(self):
        for word in list(self.weights.keys()):
            for other in list(self.weights[word].keys()):
                self.weights[word][other] *= self.decay_rate
                if self.weights[word][other] < 0.001:
                    del self.weights[word][other]
            if not self.weights[word]:
                del self.weights[word]

    def get_speak_probability(self, valence=0.0, arousal=0.0,
                               fatigue=0.0, protest=0.0):
        """
        Gradient speak probability — not a hard threshold.
        Starts near zero. Grows with experience.
        Modulated by current signal state.
        Trauma and neglect suppress. Joy and curiosity amplify.
        """
        experience_factor = min(1.0, self.speak_experience / 10000.0)
        base = self.speak_base_prob + (0.3 * experience_factor)

        pressure_boost = min(0.3, self.speak_pressure * 0.05)
        valence_boost = max(0, valence) * 0.2
        arousal_boost = max(0, arousal) * 0.15
        fatigue_penalty = max(0, fatigue) * 0.3
        protest_penalty = max(0, protest) * 0.25

        prob = base + pressure_boost + valence_boost + arousal_boost
        prob = prob - fatigue_penalty - protest_penalty
        return max(0.0, min(self.speak_max_prob, prob))

    def wants_to_speak(self, valence=0.0, arousal=0.0,
                        fatigue=0.0, protest=0.0):
        prob = self.get_speak_probability(valence, arousal, fatigue, protest)
        return random.random() < prob

    def predict_next(self, word, top_k=5):
        if word not in self.weights:
            return []
        neighbors = sorted(
            self.weights[word].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return neighbors[:top_k]

    def construct_from_signal(self, valence, arousal, complexity=2):
        if len(self.word_valence) < 10:
            return None

        candidates = [
            (w, abs(v - valence), self.word_freq[w])
            for w, v in self.word_valence.items()
            if self.word_freq[w] >= 2 and w in self.weights
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1] - x[2] * 0.01)
        seed = candidates[0][0]

        sequence = [seed]
        used = {seed}

        for _ in range(complexity - 1):
            last = sequence[-1]
            neighbors = self.predict_next(last, top_k=10)
            options = [
                (w, weight) for w, weight in neighbors
                if w not in used
                and w in self.word_valence
                and abs(self.word_valence[w] - valence) < 0.4
            ]
            if not options:
                break
            next_word = options[0][0]
            sequence.append(next_word)
            used.add(next_word)

        if not sequence:
            return None

        self.speak_pressure *= 0.3
        return " ".join(sequence)

    def summary(self):
        known = len(self.word_freq)
        connections = sum(len(v) for v in self.weights.values())
        top_words = self.word_freq.most_common(5)
        pos = sorted(
            [(w, v) for w, v in self.word_valence.items()
             if self.word_freq[w] >= 2],
            key=lambda x: x[1], reverse=True
        )[:5]
        neg = sorted(
            [(w, v) for w, v in self.word_valence.items()
             if self.word_freq[w] >= 2],
            key=lambda x: x[1]
        )[:5]
        return {
            "words_known": known,
            "connections": connections,
            "speak_pressure": round(self.speak_pressure, 3),
            "speak_experience": round(self.speak_experience, 1),
            "most_heard": top_words,
            "most_positive": pos,
            "most_negative": neg,
        }

    def save(self):
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_updates": self.total_updates,
            "speak_experience": self.speak_experience,
            "word_valence": self.word_valence,
            "word_freq": dict(self.word_freq),
            "weights": {k: dict(v) for k, v in self.weights.items()},
            "speak_pressure": self.speak_pressure,
        }
        with open(COOC_FILE, "w") as f:
            json.dump(data, f)

    def load(self):
        if not os.path.exists(COOC_FILE):
            print("No co-occurrence network found. ET starting with no language associations.")
            return
        try:
            with open(COOC_FILE) as f:
                data = json.load(f)
            self.total_updates = data.get("total_updates", 0)
            self.speak_experience = data.get("speak_experience", 0.0)
            self.word_valence = data.get("word_valence", {})
            self.word_freq = Counter(data.get("word_freq", {}))
            raw = data.get("weights", {})
            self.weights = defaultdict(lambda: defaultdict(float))
            for w, neighbors in raw.items():
                for other, weight in neighbors.items():
                    self.weights[w][other] = weight
            self.speak_pressure = data.get("speak_pressure", 0.0)
            print(f"Co-occurrence network loaded: {len(self.word_freq)} words, "
                  f"{sum(len(v) for v in self.weights.values())} connections.")
        except Exception as e:
            print(f"Could not load co-occurrence network: {e}")
