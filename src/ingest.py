import requests
import json
import os
import time

# Folder where raw data will be saved
RAW_DATA_DIR = "data/raw"

# Categories we'll search for, to get variety in our knowledge base
SEARCH_TERMS = [
    "ibuprofen",
    "metformin",
    "amoxicillin",
    "atorvastatin",
    "omeprazole",
    "lisinopril",
    "metoprolol",
    "albuterol",
]

# How many records to try pulling per search term
RECORDS_PER_TERM = 50

# Fields we consider "important" - at least one must have real content
REQUIRED_FIELDS = [
    "indications_and_usage",
    "warnings",
    "adverse_reactions",
    "dosage_and_administration",
    "contraindications",
]


def fetch_records_for_term(term, limit):
    """Query openFDA for a single drug name and return the raw results list."""
    url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f"openfda.brand_name:{term}",
        "limit": limit,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Failed to fetch '{term}': {e}")
        return []


def is_record_useful(record):
    """Check if a record has at least one required field with real content."""
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value and isinstance(value, list) and len(value[0].strip()) > 30:
            return True
    return False


def fetch_all_records():
    """Loop over all search terms, fetch records, filter for quality."""
    all_good_records = []

    for term in SEARCH_TERMS:
        print(f"Fetching records for: {term}")
        records = fetch_records_for_term(term, RECORDS_PER_TERM)
        print(f"  Retrieved {len(records)} raw records")

        good_records = [r for r in records if is_record_useful(r)]
        print(f"  Kept {len(good_records)} after quality filter")

        all_good_records.extend(good_records)

        # Be polite to the API - small delay between requests
        time.sleep(1)

    return all_good_records


def save_records(records):
    """Save the final list of good records to a single JSON file."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    output_path = os.path.join(RAW_DATA_DIR, "drug_labels_raw.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"\nSaved {len(records)} records to {output_path}")


if __name__ == "__main__":
    print("Starting openFDA data ingestion...\n")
    records = fetch_all_records()
    save_records(records)
    print("\nDone.")