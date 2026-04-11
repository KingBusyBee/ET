import random

class VoiceSystem:
    """
    ET's emergent communication scaffold.
    
    Structure: Subject + Verb + Object + Qualifier (SVOQ)
    from the original ET architecture — kept as a trellis,
    not hardcoded grammar.
    
    Words fill slots based on:
    - Current valence (positive state = positive words)
    - Current arousal (high arousal = shorter, more active)
    - Word activation strength (vivid words preferred)
    - Which slot words have appeared in most often
    
    ET doesn't understand what it's saying yet.
    It's selecting from what it knows, shaped by how it feels.
    That's pre-linguistic communication — closer to a child
    pointing at something than forming a sentence.
    
    Output appears in the ET window when signal thresholds are met.
    ET doesn't speak constantly — only when something tips it over.
    """

    def __init__(self):
        self.last_spoke_tick = 0
        self.speak_threshold = 0.3    # integrated signal needed to speak
        self.min_gap = 500            # minimum ticks between utterances
        self.utterance_history = []   # what ET has said before

    def _select_word(self, word_store, slot, valence, arousal, exclude=None):
        """
        Select a word for a given SVOQ slot.
        Weighted by valence match and activation strength.
        """
        exclude = exclude or []
        candidates = []

        for word, data in word_store.words.items():
            if word in exclude:
                continue
            if len(word) < 2:
                continue

            # Score based on:
            # 1. Activation strength — vivid words preferred
            # 2. Valence match — positive state prefers positive words
            # 3. Slot affinity — words heard in this position before
            activation_score = data["activation"]
            valence_match = 1.0 - abs(data["valence_avg"] - valence)
            slot_score = data["positions"].get(slot, 0) * 0.1

            score = (
                activation_score * 0.5 +
                valence_match * 0.3 +
                slot_score * 0.2
            )

            # Arousal affects word length preference
            # High arousal = short punchy words
            # Low arousal = longer words acceptable
            if arousal > 0.3 and len(word) > 6:
                score *= 0.7
            elif arousal < -0.3 and len(word) < 4:
                score *= 0.7

            candidates.append((word, score))

        if not candidates:
            return None

        # Weighted random selection — not pure max
        # Adds variability while still preferring high-score words
        total = sum(s for _, s in candidates)
        if total == 0:
            return random.choice([w for w, _ in candidates])

        r = random.uniform(0, total)
        running = 0
        for word, score in candidates:
            running += score
            if running >= r:
                return word

        return candidates[-1][0]

    def should_speak(self, tick, signal_state, cortical):
        """
        ET speaks when something tips it over a threshold.
        Not on a timer. Not randomly. When the signal demands it.
        """
        if tick - self.last_spoke_tick < self.min_gap:
            return False

        integrated = cortical.get_integrated_signal()
        attention = cortical.get_attention()
        valence = signal_state.get("valence", 0.0)
        connection = signal_state.get("connection", 0.0)

        # Speak when attention is high and valence is significant
        # OR when protest is very high (crying out)
        protest = signal_state.get("protest", 0.0)

        signal_pressure = (
            abs(integrated) * 0.4 +
            attention * 0.3 +
            abs(valence) * 0.2 +
            protest * 0.1
        )

        return signal_pressure >= self.speak_threshold

    def construct(self, word_store, signal_state, cortical):
        """
        Construct an utterance from current signal state.
        Find scenes that match current state, reconstruct from those scenes.
        Meaning comes from context, not individual word valence.
        """
        if word_store.scene_count() < 3:
            return None

        valence = signal_state.get("valence", 0.0)
        arousal = signal_state.get("arousal", 0.0)
        attention = cortical.get_attention()
        fatigue = signal_state.get("fatigue", 0.0)

        # Find scenes that resemble current signal state
        matching_scenes = word_store.find_scenes_for_signal(
            valence, arousal, attention, n=5
        )
        if not matching_scenes:
            return None

        # Complexity scales with arousal and attention
        complexity = max(1, int(
            1 + attention * 2 + abs(valence) * 1.0 - fatigue * 0.5
        ))
        complexity = min(4, complexity)

        # Pull words from matching scenes weighted by activation
        import random
        candidate_words = []
        for scene in matching_scenes:
            weight = scene["activation"]
            for word in scene["words"]:
                if len(word) > 2:
                    candidate_words.append((word, weight))

        if not candidate_words:
            return None

        # Select words without repetition
        selected = []
        seen = set()
        random.shuffle(candidate_words)
        candidate_words.sort(key=lambda x: x[1], reverse=True)

        for word, weight in candidate_words:
            if word not in seen and len(selected) < complexity:
                selected.append(word)
                seen.add(word)

        if not selected:
            return None

        return " ".join(selected)

    def speak(self, word_store, signal_state, cortical, tick):
        """
        Attempt to produce an utterance.
        Returns the utterance string or None.
        """
        if not self.should_speak(tick, signal_state, cortical):
            return None

        utterance = self.construct(word_store, signal_state, cortical)
        if utterance:
            self.last_spoke_tick = tick
            self.utterance_history.append({
                "tick": tick,
                "utterance": utterance,
                "valence": signal_state.get("valence", 0.0),
                "arousal": signal_state.get("arousal", 0.0),
            })
            # Keep history manageable
            if len(self.utterance_history) > 100:
                self.utterance_history = self.utterance_history[-100:]

        return utterance
