import json

with open("/home/emergent-thought/ET/et_words.json") as f:
    d = json.load(f)

words = d["words"]
print(f"Total words: {len(words)}")

sorted_pos = sorted(words.items(), key=lambda x: x[1]["valence_avg"], reverse=True)[:5]
sorted_neg = sorted(words.items(), key=lambda x: x[1]["valence_avg"])[:5]
sorted_str = sorted(words.items(), key=lambda x: x[1]["activation"], reverse=True)[:5]

print("\nMost positive associations:")
for w, data in sorted_pos:
    print(f"  {w}: {data['valence_avg']:+.3f} (heard {data['count']}x)")

print("\nMost negative associations:")
for w, data in sorted_neg:
    print(f"  {w}: {data['valence_avg']:+.3f} (heard {data['count']}x)")

print("\nStrongest activation right now:")
for w, data in sorted_str:
    print(f"  {w}: activation {data['activation']:.3f} valence {data['valence_avg']:+.3f}")

print(f"\nTotal ticks logged: {d['tick_count']}")
