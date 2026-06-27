import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.generate import generate_answer

TEST_QUESTIONS_PATH = "eval/test_questions.json"
RESULTS_OUTPUT_PATH = "eval/raw_results.json"


def load_test_questions():
    with open(TEST_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation():
    test_questions = load_test_questions()
    results = []

    for item in test_questions:
        print(f"Running {item['id']}: {item['question']}")

        output = generate_answer(item["question"])

        actual_behavior = "abstain" if "don't have enough information" in output["answer"].lower() else "answer"
        result = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_behavior": item["expected_behavior"],
            "actual_behavior": actual_behavior,
            "behavior_correct": actual_behavior == item["expected_behavior"],
            "answer": output["answer"],
            "num_sources": len(output["sources"]),
            "sources": [
                {
                    "drug_name": s["drug_name"],
                    "section_type": s["section_type"],
                    "distance": s["distance"],
                    "text": s["text"],
                }
                for s in output["sources"]
            ],
        }
        results.append(result)

    with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved {len(results)} results to {RESULTS_OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
