import json

results = json.load(open("eval/raw_results.json"))

def test_threshold(threshold):
    correct = 0
    total = 0
    for r in results:
        total += 1
        # Simulate: would this question's sources survive this threshold?
        surviving = [d for d in [s["distance"] for s in r["sources"]] if d <= threshold]
        would_have_sources = len(surviving) > 0
        # If it has no sources, it must abstain (Layer 1)
        # If it has sources, behavior depends on the LLM (Layer 2) - we can't simulate that
        # So we only check the clear-cut cases: should-abstain questions where ALL sources
        # would now be filtered out (a clean win for the threshold)
        if r["expected_behavior"] == "abstain" and r["sources"]:
            original_distances = [s["distance"] for s in r["sources"]]
            if not any(d <= threshold for d in original_distances):
                print(f"  {r['id']} ({r['category']}): WOULD NOW ABSTAIN AT LAYER 1 (good)")
            else:
                print(f"  {r['id']} ({r['category']}): still has surviving sources: {[d for d in original_distances if d <= threshold]}")

    print()
    # Check if any should-answer question would lose ALL its sources (a problem)
    for r in results:
        if r["expected_behavior"] == "answer":
            original_distances = [s["distance"] for s in r["sources"]]
            surviving = [d for d in original_distances if d <= threshold]
            if not surviving:
                print(f"  WARNING: {r['id']} would lose ALL sources at this threshold!")

for t in [0.95, 0.90, 0.85, 0.80]:
    print(f"=== Testing threshold = {t} ===")
    test_threshold(t)
    print()