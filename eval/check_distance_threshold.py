import json

results = json.load(open("eval/raw_results.json"))

print("Distances for QUESTIONS THAT SHOULD ANSWER (want LOW distance):")
for r in results:
    if r["expected_behavior"] == "answer":
        distances = [s["distance"] for s in r["sources"]]
        print(f"  {r['id']}: {distances}")

print()
print("Distances for QUESTIONS THAT SHOULD ABSTAIN (want HIGH distance, or these are false matches):")
for r in results:
    if r["expected_behavior"] == "abstain" and r["sources"]:
        distances = [s["distance"] for s in r["sources"]]
        print(f"  {r['id']} ({r['category']}): {distances}")