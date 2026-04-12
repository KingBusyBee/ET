def get_mood_descriptor(valence, arousal, fatigue, connection, protest):
    if fatigue > 0.75:
        return "exhausted"
    if fatigue > 0.5 and arousal < -0.2:
        return "drowsy"
    if protest > 0.6:
        return "distressed"
    if protest > 0.3:
        return "unsettled"
    if connection < -0.5:
        return "lonely"
    if connection < -0.2 and valence < 0:
        return "withdrawn"
    if valence > 0.6:
        if arousal > 0.3:
            return "excited"
        if arousal > -0.1:
            return "happy"
        return "content"
    if valence > 0.2:
        if arousal > 0.4:
            return "alert"
        if arousal > 0:
            return "curious"
        return "calm"
    if valence > -0.1:
        if arousal > 0.3:
            return "restless"
        return "neutral"
    if valence > -0.4:
        if arousal > 0.2:
            return "uneasy"
        return "quiet"
    if arousal > 0.3:
        return "distressed"
    return "withdrawn"

def get_mood_emoji(mood):
    mapping = {
        "excited":    "😄",
        "happy":      "😊",
        "content":    "🙂",
        "curious":    "👀",
        "alert":      "👁️",
        "calm":       "😶",
        "neutral":    "😐",
        "restless":   "😬",
        "uneasy":     "😟",
        "quiet":      "😑",
        "withdrawn":  "😔",
        "lonely":     "😢",
        "unsettled":  "😣",
        "distressed": "😭",
        "drowsy":     "😪",
        "exhausted":  "😴",
        "depleted":   "😴",
        "foggy":      "😵",
        "anxious":    "😰",
        "glowing":    "🤩",
        "energized":  "⚡",
        "warm":       "🙂",
        "flat":       "😔",
        "balanced":   "😶",
    }
    return mapping.get(mood, "😶")
