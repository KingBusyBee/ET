import json
from datetime import datetime

print("=" * 55)
print("ET Morning Report")
print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 55)

# State
try:
    with open("/home/emergent-thought/ET/et_state.json") as f:
        state = json.load(f)
    print(f"\n[Life]")
    print(f"  Total ticks:     {state['tick_count']}")
    print(f"  Interactions:    {state.get('interaction_count', '?')}")
    a = state["autonomic"]
    print(f"\n[Autonomic at rest]")
    print(f"  Arousal:  {a['arousal']:+.3f}")
    print(f"  Fatigue:  {a['fatigue']:+.3f}")
    l = state["limbic"]
    print(f"\n[Limbic]")
    print(f"  Valence:          {l['valence']:+.3f}")
    print(f"  Emotional memory: {l['emotional_memory']:+.3f}")
    s = state["social"]
    print(f"\n[Social]")
    print(f"  Connection: {s['connection']:+.3f}")
    print(f"  Trust:      {s['trust']:+.3f}")
    print(f"  Protest:    {s['protest']:+.3f}")
    att = state["attachment"]
    dominant = max(att, key=att.get)
    print(f"\n[Attachment — dominant: {dominant}]")
    for k, v in att.items():
        bar = "█" * int(abs(v) * 20)
        print(f"  {k:10}: {v:+.4f} {bar}")
except Exception as e:
    print(f"  Could not read state: {e}")

# Memory
try:
    with open("/home/emergent-thought/ET/et_memory.json") as f:
        mem = json.load(f)
    episodes = mem["episodes"]
    print(f"\n[Memory]")
    print(f"  Episodes:     {len(episodes)}")
    if episodes:
        avg_v = sum(e["valence"] for e in episodes) / len(episodes)
        avg_a = sum(e["activation"] for e in episodes) / len(episodes)
        most_r = max(episodes, key=lambda e: e["reactivation_count"])
        print(f"  Avg valence:  {avg_v:+.4f}")
        print(f"  Avg activation: {avg_a:.4f}")
        print(f"  Most reactivated: tick {most_r['tick']} ({most_r['reactivation_count']}x)")
except Exception as e:
    print(f"  Could not read memory: {e}")

# Words
try:
    with open("/home/emergent-thought/ET/et_words.json") as f:
        wd = json.load(f)
    words = wd["words"]
    print(f"\n[Vocabulary — {len(words)} words known]")

    sorted_pos = sorted(words.items(), key=lambda x: x[1]["valence_avg"], reverse=True)[:5]
    sorted_neg = sorted(words.items(), key=lambda x: x[1]["valence_avg"])[:5]
    sorted_str = sorted(words.items(), key=lambda x: x[1]["activation"], reverse=True)[:8]

    print(f"\n  Most positive:")
    for w, d in sorted_pos:
        print(f"    {w:15} {d['valence_avg']:+.3f} (heard {d['count']}x)")

    print(f"\n  Most negative:")
    for w, d in sorted_neg:
        print(f"    {w:15} {d['valence_avg']:+.3f} (heard {d['count']}x)")

    print(f"\n  Strongest right now:")
    for w, d in sorted_str:
        print(f"    {w:15} activation {d['activation']:.3f}")
except Exception as e:
    print(f"  Could not read words: {e}")

print("\n" + "=" * 55)
