# MedAssist — RAG-Powered Clinical Knowledge Assistant
### Complete Implementation Plan (Start to End)

> A retrieval-augmented generation (RAG) system that answers natural-language medical/drug questions by retrieving real FDA drug label data and generating grounded, citation-backed answers — with built-in hallucination control.

---

## 1. Project Definition

**What it is:**
A web application where a user asks a medical/drug-related question (e.g., *"What are the contraindications for metformin in patients with renal impairment?"*) and the system:

1. Searches a knowledge base of real FDA drug labels for relevant sections
2. Passes the retrieved text to an LLM as grounding context
3. Returns a generated answer **with citations** pointing back to the exact source section
4. **Abstains** ("I don't have enough information") when retrieval confidence is low, instead of letting the LLM hallucinate

**Why this matters (the pitch):**
LLMs hallucinate medical facts confidently. This project demonstrates the standard industry fix — Retrieval-Augmented Generation — applied to a domain where being wrong has real consequences, with a measured evaluation proving the grounding actually works.

**Disclaimer to include prominently in the repo:** This is an educational/portfolio project, not a clinical decision-making tool. It must not be used for real medical advice.

### Domains this single project demonstrates
| Domain | Where it shows up |
|---|---|
| NLP / Embeddings | Text-to-vector representation of medical text |
| Information Retrieval | Semantic/vector search over a knowledge base |
| Generative AI / LLMs | Prompt engineering, grounded generation |
| Responsible AI | Hallucination mitigation, abstention logic |
| Software Engineering | Modular pipeline, API integration, clean architecture |
| MLOps Basics | Containerization, deployment, environment management |
| Data Science / Evaluation | Building a test set, measuring retrieval & answer quality |

---

## 2. Architecture Overview

```
Raw FDA Drug Labels (JSON)
        |
        v
Preprocessing & Cleaning
        |
        v
Chunking (by label section, with overlap)
        |
        v
Embedding Model (sentence-transformers)
        |
        v
Vector Store (ChromaDB)
        |
        v
   [ Query Time ]
        |
User Question --> Retrieve Top-K Chunks --> LLM + Grounded Prompt --> Cited Answer
        |
        v
Streamlit Frontend (question box, answer, expandable sources)
        |
        v
Evaluation Layer (test set + accuracy/faithfulness scoring)
```

---

## 3. Dataset — Where to Get It

**Primary source: openFDA Drug Label API** (official U.S. FDA data, free, public, no auth required for moderate use)

- API documentation: `https://open.fda.gov/apis/drug/label/`
- Direct query endpoint: `https://api.fda.gov/drug/label.json?limit=100`
- Bulk download (13 zipped JSON files, if you want full offline data): `https://open.fda.gov/apis/drug/label/download/`

**Recommended approach:** Query the live API directly for 300–500 drug label records spread across a few therapeutic categories (e.g., pain relief, diabetes, cardiovascular, antibiotics). This is faster than bulk download, keeps the dataset diverse, and is itself a demonstrable skill (API integration) for your README.

**Useful fields per record (these become your chunks):**
- `indications_and_usage`
- `warnings` / `warnings_and_cautions`
- `adverse_reactions`
- `drug_interactions`
- `contraindications`
- `dosage_and_administration`

**Important note for your README:** openFDA explicitly states this data should not be relied on for actual medical decisions — cite this in your disclaimer.

---

## 4. Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Data source | openFDA Drug Label API | Free, official, structured, real-world |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, fast, strong baseline |
| Vector DB | ChromaDB | Free, local, simple persistence |
| LLM | Groq API (Llama 3.1) or OpenAI API | Free/cheap, fast inference |
| Orchestration | Plain Python (no LangChain) | Shows you understand RAG internals, not just a framework |
| Frontend | Streamlit | Fast to build, clean to demo |
| Containerization | Docker | Shows deployment maturity |
| Deployment | Streamlit Community Cloud / Hugging Face Spaces | Free hosting |

---

## 5. Step-by-Step Build Plan (10 Days)

### Phase 0 — Setup (Day 1, ~2 hrs)
- Create GitHub repo with full folder structure from day one (see Section 6)
- Set up Python virtual environment
- Get free API key (Groq recommended for free Llama access)
- Create `.env.example` — never commit real keys

### Phase 1 — Data Collection (Day 1–2)
- Pull 300–500 records from the openFDA API across multiple drug categories
- Save raw JSON to `data/raw/`
- Run a basic data quality check: missing fields, duplicate entries, encoding issues

### Phase 2 — Preprocessing & Chunking (Day 2–3)
- Parse each label into its labeled sections
- Chunk by **section boundary** (not arbitrary token splitting) — ~300–500 tokens per chunk, with slight overlap
- Tag every chunk with metadata: `{drug_name, section_type, source_id}`
- This metadata is what makes citations possible later — don't skip it

### Phase 3 — Embedding + Vector Store (Day 3–4)
- Embed all chunks using `sentence-transformers`
- Store embeddings + metadata in ChromaDB (persisted to disk)
- Manually test retrieval with 5–10 sample queries before moving on — confirm it's actually returning relevant chunks

### Phase 4 — Generation Layer (Day 4–6)
- Design a prompt template that forces the LLM to:
  - Answer **only** from the provided retrieved context
  - Cite which chunk/drug/section supports each claim
  - Explicitly say "I don't have enough information" when retrieved context is weak/irrelevant
- Wire up the LLM API call (Groq or OpenAI)
- This is the core engineering logic of the whole project — spend the most care here

### Phase 5 — Evaluation (Day 6–7) — *the differentiator most people skip*
- Manually build a test set of 20–25 questions:
  - Mix of clearly answerable questions and intentionally unanswerable ones (to test abstention)
- Measure and record:
  - Retrieval accuracy (did it pull the correct chunk?)
  - Answer faithfulness (manual check: does the answer match the source?)
  - Abstention correctness (did it say "I don't know" appropriately?)
- Save results as a table in `eval/results.md` — this is what makes the project look rigorous rather than a tutorial clone

### Phase 6 — Frontend (Day 7–8)
- Build a Streamlit UI: search box, generated answer, expandable "Sources" section showing the exact retrieved text and drug name
- Add a sidebar listing which drug categories are in the knowledge base

### Phase 7 — Deployment (Day 8–9)
- Write a `Dockerfile` (even if final deployment is on Streamlit Cloud — shows engineering maturity)
- Deploy to Streamlit Community Cloud or Hugging Face Spaces (both free)

### Phase 8 — Documentation & Polish (Day 9–10)
- Write a professional `README.md`: architecture diagram, setup instructions, demo GIF/screenshot, evaluation results table
- Clean, meaningful commit history (commit as you go through each phase — not one giant final commit)
- Add `LICENSE`, finalize `requirements.txt`, finalize `.gitignore`

---

## 6. GitHub Repository Structure

```
medassist-rag/
├── README.md
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── ingest.py          # pulls data from the openFDA API
│   ├── preprocess.py      # cleaning + chunking
│   ├── embed.py           # embedding + vector store creation
│   ├── retrieve.py        # retrieval logic
│   ├── generate.py        # LLM prompting + citation logic
│   └── pipeline.py        # ties the full pipeline together
├── eval/
│   ├── test_questions.json
│   ├── evaluate.py
│   └── results.md
├── app.py                 # Streamlit frontend
└── notebooks/
    └── exploration.ipynb  # initial exploratory work
```

---

## 7. Resume / LinkedIn Bullet (once complete)

> Built and deployed a RAG-based clinical knowledge assistant achieving X% citation accuracy on a custom evaluation set, using ChromaDB, sentence-transformer embeddings, and Llama 3.1 — with hallucination-aware abstention for low-confidence queries.

(Fill in X% once Phase 5 evaluation results are in.)

---

## 8. Honesty Notes for Interviews

- This is a **portfolio/demo system**, not a medical-grade product. State this explicitly in the README — it reads as responsible AI awareness, not a weakness.
- Phase 5 (evaluation) is the most commonly skipped step under time pressure. It takes ~1 day and disproportionately raises the credibility of the whole project — do not cut it.

---

## 9. Next Steps

Implementation begins with **Phase 1 — Data Collection** (`src/ingest.py`), pulling real records from the openFDA API.
