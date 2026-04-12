import json
from datetime import datetime

print("=" * 55)
print("ET Morning Report")
print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 55)

try:
    with open("/home/emergent-thought/ET/et_state.json") as f:
        state = json.load(f)
    print(f"\n[Life]")
    print(f"  Total ticks:     {state['tick_count']}")
    a = state["autonomic"]
    l = state["limbic"]
    s = state["social"]
    att = state["attachment"]
    print(f"\n[Autonomic]")
    print(f"  Arousal:  {a['arousal']:+.3f}  Fatigue: {a['fatigue']:+.3f}")
    print(f"\n[Limbic]")
    print(f"  Valence: {l['valence']:+.3f}  Memory: {l['emotional_memory']:+.3f}")
    print(f"\n[Social]")
    print(f"  Connection: {s['connection']:+.3f}  Trust: {s['trust']:+.3f}  Protest: {s['protest']:+.3f}")
    dominant = max(att, key=att.get)
    print(f"\n[Attachment — {dominant}]")
    for k, v in att.items():
        bar = "█" * int(abs(v) * 200)
        print(f"  {k:10}: {v:+.4f} {bar}")
except Exception as e:
    print(f"State error: {e}")

try:
    with open("/home/emergent-thought/ET/et_memory.json") as f:
        mem = json.load(f)
    episodes = mem["episodes"]
    print(f"\n[Memory — {len(episodes)} episodes]")
    if episodes:
        avg_v = sum(e["valence"] for e in episodes) / len(episodes)
        print(f"  Avg valence: {avg_v:+.4f}")
        high = sorted(episodes, key=lambda e: abs(e["valence"]), reverse=True)[:3]
        print(f"  Most significant moments:")
        for ep in high:
            print(f"    tick {ep['tick']:5d}  valence {ep['valence']:+.3f}  reactivated {ep['reactivation_count']}x")
except Exception as e:
    print(f"Memory error: {e}")

try:
    with open("/home/emergent-thought/ET/et_scenes.json") as f:
        wd = json.load(f)
    words = wd["words"]
    print(f"\n[Vocabulary — {len(words)} words known]")

    scenes = wd.get("scenes", [])
    if not scenes:
        print("  No scenes yet.")
        raise Exception("no scenes")
    sorted_str = sorted(scenes, key=lambda x: x["activation"], reverse=True)[:5]
    sorted_cnt = sorted(scenes, key=lambda x: x["reactivations"], reverse=True)[:5]

    print(f"\n  Most heard:")
    for w, d in sorted_cnt:
        print(f"    {w:15} {d['count']}x  valence {d['valence_avg']:+.3f}")

    print(f"\n  Most positive associations:")
    for w, d in sorted_pos:
        print(f"    {w:15} {d['valence_avg']:+.3f}  heard {d['count']}x")

    print(f"\n  Most negative associations:")
    for w, d in sorted_neg:
        print(f"    {w:15} {d['valence_avg']:+.3f}  heard {d['count']}x")

    print(f"\n  Strongest activation now:")
    for w, d in sorted_str:
        print(f"    {w:15} {d['activation']:.3f}")

    # Show words from your conversation specifically
    your_words = ["hi", "love", "et", "up", "what"]
    print(f"\n  Words from your conversation:")
    for w in your_words:
        if w in words:
            d = words[w]
            print(f"    {w:15} valence {d['valence_avg']:+.3f}  heard {d['count']}x  activation {d['activation']:.3f}")
        else:
            print(f"    {w:15} not yet known")

except Exception as e:
    print(f"Word error: {e}")

try:
    with open("/home/emergent-thought/ET/et_scenes.json") as f:
        wd = json.load(f)
    if wd.get("words"):
        vh = [(w, d) for w, d in wd["words"].items() if d["count"] >= 2]
        if vh:
            print(f"\n[Voice history — what ET could say]")
            top = sorted(vh, key=lambda x: x[1]["activation"], reverse=True)[:5]
            print(f"  Highest activation words (ET's current vocabulary):")
            for w, d in top:
                print(f"    {w:15} activation {d['activation']:.3f}  valence {d['valence_avg']:+.3f}")
except:
    pass

print("\n" + "=" * 55)
