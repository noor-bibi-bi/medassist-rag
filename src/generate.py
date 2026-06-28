import os
import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "llama-3.1-8b-instant"

CHROMA_DB_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "medassist_chunks"
TOP_K = 5
MAX_DISTANCE_THRESHOLD = 0.85  # chunks worse than this are considered irrelevant

SYSTEM_PROMPT = """You are a medical information assistant. You must follow these rules strictly:

1. Answer ONLY using the provided context below. Do not use any outside knowledge, even if you know it.
2. For every claim you make, cite the source using [Source N] notation, where N matches the source number in the context.
3. If the context does not contain enough information to answer the question, your ENTIRE response must be exactly this sentence and nothing else: "I don't have enough information in my knowledge base to answer this question confidently. Please consult a healthcare professional." If you provide any real information from the context first, you have already answered - in that case, do not also include this sentence anywhere in your response, even as a closing disclaimer.
4. Do not give medical advice beyond what is explicitly stated in the context. Do not add general health tips, interpretations, or extrapolations.
5. Write in clear, plain language a patient could understand - not clinical excerpt style. Use short paragraphs or simple, single-level bullet points (no nested or indented sub-bullets) when listing multiple items. Each bullet should be a complete, standalone point - never repeat the same phrase across multiple nested levels. Keep it focused and concise, but human-readable, not a dense block of medical jargon.
6. If the question does not name a specific drug or condition, and the context only matches by loose keyword similarity rather than directly addressing the question, you MUST use the exact refusal sentence from rule 3. Do not assume the question is about whichever drug happens to appear in the context. Partial relevance is not enough - if the context does not directly and specifically answer what was asked, refuse rather than hedge or guess."""

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_collection(COLLECTION_NAME)


def build_context_string(retrieved_chunks):
    """
    Takes a list of retrieved chunk dicts (with 'text' and metadata) and
    formats them into a numbered context block for the prompt.
    """
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        source_line = f"[Source {i}] Drug: {chunk['drug_name']} | Section: {chunk['section_type']}"
        if chunk.get("subheader"):
            source_line += f" | Subheader: {chunk['subheader']}"
        context_parts.append(f"{source_line}\n\"{chunk['text']}\"")

    return "\n\n".join(context_parts)


def build_user_prompt(question, retrieved_chunks):
    """Combines the context and question into the final prompt sent to the LLM."""
    context_string = build_context_string(retrieved_chunks)
    return f"""CONTEXT:
{context_string}

QUESTION: {question}

ANSWER:"""


def retrieve_relevant_chunks(question, top_k=TOP_K):
    """
    Embeds the question, queries ChromaDB, and returns a list of relevant
    chunk dicts. Filters out chunks whose distance is too high (i.e., not
    actually relevant) - this is our Layer 1 defense against hallucination.
    """
    query_embedding = embedding_model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]

        if distance > MAX_DISTANCE_THRESHOLD:
            continue  # skip chunks that are too dissimilar to be useful

        metadata = results["metadatas"][0][i]
        chunks.append({
            "drug_name": metadata["drug_name"],
            "manufacturer": metadata["manufacturer"],
            "section_type": metadata["section_type"],
            "subheader": metadata["subheader"],
            "source_id": metadata["source_id"],
            "text": results["documents"][0][i],
            "distance": distance,
        })

    deduplicated_chunks = deduplicate_chunks(chunks)
    return deduplicated_chunks


def deduplicate_chunks(chunks):
    """
    Collapses near-duplicate chunks (same drug + section, highly similar text)
    down to one representative chunk - the one with the lowest distance.
    Chunks are already sorted by distance (best first) from ChromaDB, so the
    first occurrence of each (drug, section, text-prefix) key is the best one.
    """
    seen_keys = set()
    deduplicated = []

    for chunk in chunks:
        # Use first 100 chars of text as a fingerprint - near-identical chunks
        # (different manufacturers, same boilerplate wording) will share this
        text_fingerprint = chunk["text"][:100].strip().lower()
        key = (chunk["drug_name"].strip().lower(), chunk["section_type"], text_fingerprint)

        if key in seen_keys:
            continue

        seen_keys.add(key)
        deduplicated.append(chunk)

    return deduplicated


def generate_answer(question):
    """
    Full pipeline: retrieve relevant chunks, build the prompt, call the LLM,
    and return both the answer and the chunks used (for citation display).
    """
    relevant_chunks = retrieve_relevant_chunks(question)

    if not relevant_chunks:
        return {
            "answer": "I don't have enough information in my knowledge base to answer this question confidently. Please consult a healthcare professional.",
            "sources": [],
        }

    user_prompt = build_user_prompt(question, relevant_chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    answer_text = response.choices[0].message.content

    return {
        "answer": answer_text,
        "sources": relevant_chunks,
    }


if __name__ == "__main__":
    test_questions = [
        "Can I take metformin if I have kidney problems?",
        "What is the capital of France?",
        "Will ibuprofen interact with my cat's medication?",
    ]

    for test_question in test_questions:
        result = generate_answer(test_question)
        print(f"QUESTION: {test_question}")
        print(f"ANSWER:\n{result['answer']}\n")
        print(f"SOURCES USED: {len(result['sources'])}")
        for i, source in enumerate(result['sources'], start=1):
            print(f"  [{i}] {source['drug_name']} | {source['section_type']} | distance: {source['distance']:.4f}")
        print("\n" + "="*80 + "\n")