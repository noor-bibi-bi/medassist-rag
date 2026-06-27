import json
from collections import defaultdict

RESULTS_PATH = "eval/raw_results.json"


def analyze():
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    correct = sum(1 for r in results if r["behavior_correct"])
    total = len(results)
    print(f"Overall behavior accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print()

    by_category = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        by_category[r["category"]]["total"] += 1
        if r["behavior_correct"]:
            by_category[r["category"]]["correct"] += 1

    print("Accuracy by category:")
    for cat, stats in by_category.items():
        print(f"  {cat}: {stats['correct']}/{stats['total']}")

    print()
    print("Questions where behavior was WRONG:")
    wrong_count = 0
    for r in results:
        if not r["behavior_correct"]:
            wrong_count += 1
            print(f"  {r['id']}: expected={r['expected_behavior']}, actual={r['actual_behavior']} | {r['question']}")

    if wrong_count == 0:
        print("  (none)")

def inspect_question(question_id):
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    match = [r for r in results if r["id"] == question_id]
    if not match:
        print(f"No result found for {question_id}")
        return

    r = match[0]
    print(f"QUESTION: {r['question']}")
    print(f"EXPECTED: {r['expected_behavior']} | ACTUAL: {r['actual_behavior']}")
    print(f"\nANSWER:\n{r['answer']}\n")
    print(f"NUM SOURCES: {r['num_sources']}")
    for s in r['sources']:
        print(f"  {s['drug_name']} | {s['section_type']} | distance: {s['distance']:.4f}")
        print(f"    Text: {s['text'][:200]}")
if __name__ == "__main__":
    analyze()
    print("\n" + "="*80 + "\n")
    inspect_question("Q11")
if __name__ == "__main__":
    analyze()
    print("\n" + "="*80 + "\n")
    inspect_question("Q18")
    print("\n" + "="*80 + "\n")
    inspect_question("Q22")
    print("\n" + "="*80 + "\n")
    inspect_question("Q25")
    inspect_question("Q04")