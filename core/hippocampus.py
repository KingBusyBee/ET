import json
import os
import math
from collections import deque
from datetime import datetime

class Hippocampus:
    """
    ET's hippocampal rolling context — short-term episodic binding.
    
    Biologically: the hippocampus maintains a rolling context of recent
    experience, feeding back into itself. Each new moment is interpreted
    in light of recent moments. This is how we hold the thread of a 
    conversation, a story, a task.
    
    Architecture: small RNN with 4 context slots (working memory limit).
    Each slot holds a compressed signal state from a recent scene.
    The rolling context influences what gets encoded and what gets recalled.
    
    Hebbian learning: connections between frequently co-occurring signal
    patterns strengthen over time. ET literally rewires based on experience.
    """

    def __init__(self, context_size=4, hidden_size=8):
        self.context_size = context_size  # working memory slots
        self.hidden_size = hidden_size    # RNN hidden units

        # Rolling context — last N scene signal states
        self.context = deque(maxlen=context_size)

        # RNN weights — small, CPU-friendly
        # Input: signal state (valence, arousal, attention, connection) = 4 values
        # Hidden: context_size * hidden_size
        # Output: prediction of next signal state = 4 values
        self.input_size = 4

        # Initialize weights small and random-ish
        self.W_ih = self._init_weights(self.hidden_size, self.input_size)   # input->hidden
        self.W_hh = self._init_weights(self.hidden_size, self.hidden_size)  # hidden->hidden
        self.W_ho = self._init_weights(self.input_size, self.hidden_size)   # hidden->output
        self.hidden = [0.0] * self.hidden_size

        # Hebbian connection strengths between signal patterns
        # key: (pattern_a_id, pattern_b_id) -> strength
        self.hebbian_connections = {}
        self.hebbian_decay = 0.0001
        self.hebbian_boost = 0.01

        # SVOQ frequency tracking — fluid, not rigid
        # word -> {subject: n, verb: n, object: n, qualifier: n}
        self.svoq_patterns = {}

        self.tick_count = 0

    def _init_weights(self, rows, cols):
        import random
        return [[random.gauss(0, 0.1) for _ in range(cols)] for _ in range(rows)]

    def _tanh(self, x):
        return math.tanh(max(-10, min(10, x)))

    def _forward(self, signal_vector):
        """One RNN step — update hidden state from input."""
        # hidden = tanh(W_ih * input + W_hh * hidden)
        new_hidden = []
        for i in range(self.hidden_size):
            h_sum = sum(self.W_ih[i][j] * signal_vector[j] for j in range(self.input_size))
            h_sum += sum(self.W_hh[i][j] * self.hidden[j] for j in range(self.hidden_size))
            new_hidden.append(self._tanh(h_sum))
        self.hidden = new_hidden

        # output = W_ho * hidden (prediction of next signal state)
        output = []
        for i in range(self.input_size):
            o_sum = sum(self.W_ho[i][j] * self.hidden[j] for j in range(self.hidden_size))
            output.append(self._tanh(o_sum))

        return output

    def _signal_to_vector(self, signal_state):
        return [
            signal_state.get("valence", 0.0),
            signal_state.get("arousal", 0.0),
            signal_state.get("attention", 0.0),
            signal_state.get("connection", 0.0),
        ]

    def encode(self, signal_state, scene_text=""):
        """
        Encode a new moment into rolling context.
        Run RNN forward pass.
        Update Hebbian connections.
        Detect SVOQ patterns from text.
        """
        self.tick_count += 1
        vector = self._signal_to_vector(signal_state)

        # RNN forward pass — predict next state
        prediction = self._forward(vector)

        # Compute surprise — how different was reality from prediction
        surprise = sum(abs(vector[i] - prediction[i]) for i in range(self.input_size)) / self.input_size

        # Store in rolling context
        context_entry = {
            "signal": signal_state,
            "vector": vector,
            "prediction": prediction,
            "surprise": surprise,
            "text": scene_text[:80],
            "tick": self.tick_count,
        }
        self.context.append(context_entry)

        # Hebbian learning — strengthen connections between recent co-active patterns
        if len(self.context) >= 2:
            prev = list(self.context)[-2]
            curr = list(self.context)[-1]
            self._update_hebbian(prev["signal"], curr["signal"])

        # SVOQ pattern detection from text
        if scene_text:
            self._detect_svoq(scene_text, signal_state)

        return surprise, prediction

    def _update_hebbian(self, signal_a, signal_b):
        """
        Strengthen connection between co-occurring signal states.
        Hebbian: neurons that fire together wire together.
        """
        # Quantize signals to pattern IDs (rough buckets)
        def quantize(s):
            v = int(s.get("valence", 0.0) * 5) / 5.0
            a = int(s.get("arousal", 0.0) * 5) / 5.0
            return (v, a)

        pa = quantize(signal_a)
        pb = quantize(signal_b)
        key = (pa, pb) if pa <= pb else (pb, pa)

        if key not in self.hebbian_connections:
            self.hebbian_connections[key] = 0.0
        self.hebbian_connections[key] = min(1.0,
            self.hebbian_connections[key] + self.hebbian_boost
        )

        # Decay all connections slightly
        if self.tick_count % 100 == 0:
            to_remove = []
            for k in self.hebbian_connections:
                self.hebbian_connections[k] -= self.hebbian_decay
                if self.hebbian_connections[k] <= 0:
                    to_remove.append(k)
            for k in to_remove:
                del self.hebbian_connections[k]

    def _detect_svoq(self, text, signal_state):
        """
        Fluid SVOQ detection — positional but frequency-weighted.
        Words that consistently appear in a position build affinity for it.
        No rigid rules — probability distributions that shift with experience.
        """
        import re
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text)]
        if len(words) < 2:
            return

        # Positional assignment — fluid, weighted by frequency
        # Short sentences: subject, verb
        # Medium: subject, verb, object  
        # Long: subject, verb, object, qualifier
        slots = ["subject", "verb", "object", "qualifier"]
        assigned = {}

        for i, word in enumerate(words[:4]):
            slot_idx = min(i, len(slots) - 1)
            # But check if this word has stronger affinity for another slot
            if word in self.svoq_patterns:
                affinities = self.svoq_patterns[word]
                best_slot = max(affinities, key=affinities.get)
                # Only override if affinity is strong enough
                total = sum(affinities.values())
                if total > 5 and affinities[best_slot] / total > 0.6:
                    slot_idx = slots.index(best_slot)

            slot = slots[slot_idx]
            assigned[word] = slot

            if word not in self.svoq_patterns:
                self.svoq_patterns[word] = {s: 0 for s in slots}
            self.svoq_patterns[word][slot] += 1

    def get_context_summary(self):
        """What is ET currently holding in working memory?"""
        if not self.context:
            return []
        return [
            {
                "text": e["text"],
                "valence": round(e["signal"].get("valence", 0.0), 3),
                "surprise": round(e["surprise"], 3),
            }
            for e in list(self.context)
        ]

    def get_prediction(self):
        """What does ET predict will happen next?"""
        if not self.context:
            return None
        return list(self.context)[-1]["prediction"]

    def get_strongest_patterns(self, n=5):
        """What signal co-occurrences has ET learned most strongly?"""
        sorted_h = sorted(
            self.hebbian_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_h[:n]

    def get_svoq_for_word(self, word):
        """What SVOQ role does ET associate with this word?"""
        if word not in self.svoq_patterns:
            return None
        affinities = self.svoq_patterns[word]
        total = sum(affinities.values())
        if total == 0:
            return None
        return {slot: count/total for slot, count in affinities.items()}

    def save(self, path):
        data = {
            "tick_count": self.tick_count,
            "W_ih": self.W_ih,
            "W_hh": self.W_hh,
            "W_ho": self.W_ho,
            "hidden": self.hidden,
            "hebbian_connections": {str(k): v for k, v in self.hebbian_connections.items()},
            "svoq_patterns": self.svoq_patterns,
            "context": list(self.context),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path):
        if not os.path.exists(path):
            print("No hippocampus state found. Starting fresh.")
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self.tick_count = data.get("tick_count", 0)
            self.W_ih = data.get("W_ih", self.W_ih)
            self.W_hh = data.get("W_hh", self.W_hh)
            self.W_ho = data.get("W_ho", self.W_ho)
            self.hidden = data.get("hidden", self.hidden)
            self.svoq_patterns = data.get("svoq_patterns", {})
            # Rebuild hebbian connections
            raw = data.get("hebbian_connections", {})
            self.hebbian_connections = {}
            for k, v in raw.items():
                try:
                    self.hebbian_connections[eval(k)] = v
                except:
                    pass
            context_data = data.get("context", [])
            self.context = deque(context_data, maxlen=self.context_size)
            print(f"Hippocampus loaded: {len(self.svoq_patterns)} SVOQ patterns, {len(self.hebbian_connections)} Hebbian connections.")
        except Exception as e:
            print(f"Could not load hippocampus: {e}")
