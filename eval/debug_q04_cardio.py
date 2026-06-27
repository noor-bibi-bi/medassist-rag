import json

chunks = json.load(open("data/processed/chunks.json"))
atorvastatin_chunks = [c for c in chunks if "atorvastatin" in c["drug_name"].lower()]

cardio_chunks = [c for c in atorvastatin_chunks if "cardiovascular" in c["subheader"].lower()]
print(f"Atorvastatin chunks with 'cardiovascular' in subheader: {len(cardio_chunks)}")
for c in cardio_chunks[:3]:
    print(f"  drug={c['drug_name']!r} | subheader={c['subheader']!r}")
    print(f"  text={c['text'][:200]!r}")
    print()

single_word_chunks = [c for c in atorvastatin_chunks if len(c['text'].split()) <= 2]
print(f"Atorvastatin chunks with 2 words or fewer: {len(single_word_chunks)}")