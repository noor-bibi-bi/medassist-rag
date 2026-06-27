import json
import os
import re

RAW_DATA_PATH = "data/raw/drug_labels_raw.json"
PROCESSED_DATA_DIR = "data/processed"

REQUIRED_FIELDS = [
    "indications_and_usage",
    "warnings",
    "adverse_reactions",
    "dosage_and_administration",
    "contraindications",
]

# Approximate chunk size in words (proxy for tokens - good enough for our purposes)
TARGET_CHUNK_WORDS = 350
OVERLAP_WORDS = 50


def get_field_text(record, field_name):
    """Safely extract text from a field, handling the list-vs-string quirk."""
    value = record.get(field_name)
    if not value:
        return ""
    if isinstance(value, list):
        return " ".join(value)
    return str(value)


def get_drug_name(record):
    """Safely extract brand name from openfda metadata."""
    openfda = record.get("openfda", {})
    brand_names = openfda.get("brand_name", [])
    if brand_names:
        return brand_names[0]
    return "Unknown Drug"


def get_manufacturer(record):
    """Safely extract manufacturer name from openfda metadata."""
    openfda = record.get("openfda", {})
    manufacturers = openfda.get("manufacturer_name", [])
    if manufacturers:
        return manufacturers[0]
    return "Unknown Manufacturer"
def split_on_subheaders(text):
    """
    Try to split text on natural sub-headers. Handles two real-world patterns
    found in FDA labels:
      1. "Allergy alert:" - Capitalized phrase ending in a colon
      2. "GASTROINTESTINAL" - ALL CAPS body-system headers (no colon),
         common in adverse_reactions sections
    Returns a list of (subheader, text) tuples.
    If no sub-headers are found, returns [("", full_text)] as a fallback.
    """
    # Pattern 1: "Capitalized phrase:" style headers
    pattern_colon = r'([A-Z][a-zA-Z ]{2,40}:)\s'

    # Pattern 2: ALL CAPS word(s), 1-4 words, standalone (e.g. "GASTROINTESTINAL",
    # "CENTRAL NERVOUS SYSTEM"). Requires at least 4 letters to avoid matching
    # short acronyms like "FDA" or single capital letters mid-sentence.
    BOILERPLATE_HEADERS = {
    "ADVERSE REACTIONS",
    "SUSPECTED ADVERSE REACTIONS",
    "WARNINGS",
    "PRECAUTIONS",
    "CONTRAINDICATIONS",
    "WARNINGS AND PRECAUTIONS",
    "DOSAGE AND ADMINISTRATION",
    "INDICATIONS AND USAGE",
    "CLINICAL STUDIES",
    "CLINICAL PHARMACOLOGY",
}
    pattern_caps = r'(?<![a-zA-Z])([A-Z]{4,}(?:\s[A-Z]{2,}){0,3})(?![a-zA-Z])'

    combined_pattern = f'(?:{pattern_colon})|(?:{pattern_caps})'
    raw_matches = list(re.finditer(combined_pattern, text))

    if len(raw_matches) < 2:
        return [("", text.strip())]

    # Build sections from ALL matches first, so no text ever gets orphaned -
    # even text that follows a boilerplate header we plan to drop.
    raw_sections = []
    for i, match in enumerate(raw_matches):
        header = (match.group(1) or match.group(2)).strip()
        start = match.end()
        end = raw_matches[i + 1].start() if i + 1 < len(raw_matches) else len(text)
        section_text = text[start:end].strip()
        raw_sections.append((header, section_text))

    # Now merge boilerplate headers into the following section, keeping the
    # text but dropping the meaningless label.
    sections = []
    for header, section_text in raw_sections:
        clean_header = header.rstrip(":")
        if clean_header in BOILERPLATE_HEADERS:
            if sections:
                # Append this boilerplate section's text onto the previous section
                prev_header, prev_text = sections[-1]
                sections[-1] = (prev_header, f"{prev_text} {section_text}".strip())
            else:
                # No previous section yet - keep it as an untitled leading section
                sections.append(("", section_text))
        else:
            sections.append((header, section_text))

    return [(h, t) for h, t in sections if t]

def chunk_text(text, target_words=TARGET_CHUNK_WORDS, overlap_words=OVERLAP_WORDS):
    """
    Split text into fixed-size word chunks with overlap.
    Used as a fallback when no natural sub-headers exist, or when a
    sub-header section is still too long on its own.
    """
    words = text.split()
    if len(words) <= target_words:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(words):
        end = start + target_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start = end - overlap_words  # step back for overlap

    return chunks


def build_chunks_for_field(field_text, field_name):
    """
    Combines sub-header splitting with fixed-size fallback chunking.
    Returns a list of (subheader_or_empty, chunk_text) tuples.
    """
    final_chunks = []
    sections = split_on_subheaders(field_text)

    for header, section_text in sections:
        # Even within a sub-header section, if it's still too long, split further
        sub_chunks = chunk_text(section_text)
        for sub_chunk in sub_chunks:
            final_chunks.append((header, sub_chunk))

    return final_chunks
def process_all_records():
    """
    Load raw records, extract relevant fields, chunk them, and attach metadata.
    Returns a list of chunk dictionaries ready for embedding.
    """
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    all_chunks = []
    chunk_counter = 0

    for record in raw_records:
        drug_name = get_drug_name(record)
        manufacturer = get_manufacturer(record)
        source_id = record.get("id", "unknown_id")

        for field_name in REQUIRED_FIELDS:
            field_text = get_field_text(record, field_name)
            if not field_text or len(field_text.strip()) < 30:
                continue  # skip empty/near-empty fields, same filter logic as Phase 1

            field_chunks = build_chunks_for_field(field_text, field_name)

            for header, chunk_body in field_chunks:
                chunk_counter += 1
                chunk_record = {
                    "chunk_id": f"chunk_{chunk_counter:05d}",
                    "drug_name": drug_name,
                    "manufacturer": manufacturer,
                    "section_type": field_name,
                    "subheader": header,
                    "source_id": source_id,
                    "text": chunk_body,
                }
                all_chunks.append(chunk_record)

    return all_chunks


def save_chunks(chunks):
    """Save the final chunked dataset to disk."""
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    output_path = os.path.join(PROCESSED_DATA_DIR, "chunks.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    print("Starting preprocessing and chunking...\n")
    chunks = process_all_records()
    save_chunks(chunks)

    # Quick sanity stats
    section_counts = {}
    for c in chunks:
        section_counts[c["section_type"]] = section_counts.get(c["section_type"], 0) + 1

    print("\nChunks per section type:")
    for section, count in section_counts.items():
        print(f"  {section}: {count}")

    print(f"\nTotal chunks: {len(chunks)}")
    print("Done.")