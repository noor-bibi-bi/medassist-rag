import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DB_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "medassist_chunks"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(COLLECTION_NAME)

query = "What are the cardiovascular side effects of atorvastatin?"
query_embedding = model.encode([query]).tolist()

results = collection.query(query_embeddings=query_embedding, n_results=10)

for i in range(len(results["ids"][0])):
    print(f"{i+1}. distance={results['distances'][0][i]:.4f} | {results['metadatas'][0][i]['drug_name']} | {results['metadatas'][0][i]['section_type']} | subheader={results['metadatas'][0][i]['subheader']!r}")
    print(f"   text: {results['documents'][0][i][:100]}")