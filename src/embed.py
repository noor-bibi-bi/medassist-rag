import json
import chromadb
from sentence_transformers import SentenceTransformer

PROCESSED_CHUNKS_PATH = "data/processed/chunks.json"
CHROMA_DB_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "medassist_chunks"
BATCH_SIZE = 100


def load_chunks():
    with open(PROCESSED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_vector_store():
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Loading chunks...")
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks.\n")

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Start fresh each time we rebuild, to avoid duplicate entries
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    print(f"Embedding and storing {len(chunks)} chunks in batches of {BATCH_SIZE}...\n")

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {
                "drug_name": c["drug_name"],
                "manufacturer": c["manufacturer"],
                "section_type": c["section_type"],
                "subheader": c["subheader"],
                "source_id": c["source_id"],
            }
            for c in batch
        ]

        embeddings = model.encode(texts).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        print(f"  Processed {min(i + BATCH_SIZE, len(chunks))} / {len(chunks)} chunks")

    print(f"\nDone. Collection '{COLLECTION_NAME}' now has {collection.count()} items.")


if __name__ == "__main__":
    build_vector_store()