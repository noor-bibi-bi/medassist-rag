import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DB_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "medassist_chunks"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(COLLECTION_NAME)

query = "Can I take metformin if I have kidney problems?"
query_embedding = model.encode([query]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=5
)

print(f"Query: {query}\n")
for i in range(len(results["ids"][0])):
    chunk_id = results["ids"][0][i]
    distance = results["distances"][0][i]
    metadata = results["metadatas"][0][i]
    document = results["documents"][0][i]

    print(f"Result {i+1} (distance: {distance:.4f})")
    print(f"  Drug: {metadata['drug_name']} | Section: {metadata['section_type']} | Subheader: {metadata['subheader']}")
    print(f"  Text: {document[:150]}...")
    print()