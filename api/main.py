import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.generate import generate_answer

app = FastAPI(title="MedAssist RAG API")

# Allow the React dev server (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TEMPORARY - will lock down to deployed frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(request: QuestionRequest):
    result = generate_answer(request.question)
    return {
        "answer": result["answer"],
        "sources": [
            {
                "drug_name": s["drug_name"],
                "manufacturer": s["manufacturer"],
                "section_type": s["section_type"],
                "subheader": s["subheader"],
                "text": s["text"],
                "distance": s["distance"],
            }
            for s in result["sources"]
        ],
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
