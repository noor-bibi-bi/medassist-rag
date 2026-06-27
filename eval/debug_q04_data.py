import json

chunks = json.load(open("data/processed/chunks.json"))

atorvastatin_chunks = [c for c in chunks if "atorvastatin" in c["drug_name"].lower()]
print(f"Total atorvastatin chunks: {len(atorvastatin_chunks)}")
print()

from collections import Counter
section_counts = Counter(c["section_type"] for c in atorvastatin_chunks)
print("By section type:")
for section, count in section_counts.items():
    print(f"  {section}: {count}")

print()
print("Sample of 'indications_and_usage' chunks for atorvastatin:")
indications_chunks = [c for c in atorvastatin_chunks if c["section_type"] == "indications_and_usage"]
for c in indications_chunks[:5]:
    print(f"  text={c['text']!r}")

print()
print("Sample of 'adverse_reactions' chunks for atorvastatin (looking for cardiovascular content):")
adverse_chunks = [c for c in atorvastatin_chunks if c["section_type"] == "adverse_reactions"]
print(f"  Total adverse_reactions chunks: {len(adverse_chunks)}")
for c in adverse_chunks[:5]:
    print(f"  subheader={c['subheader']!r} | text preview={c['text'][:100]!r}")