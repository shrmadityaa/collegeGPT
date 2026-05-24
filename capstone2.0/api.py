from fastapi import FastAPI
from pydantic import BaseModel

from retrieval.hybrid import hybrid_search
from llm.generator import generate_answer

app = FastAPI(title="CollegeGPT API")


# Request schema
class QueryRequest(BaseModel):
    query: str


# Health check
@app.get("/")
def read_root():
    return {"message": "CollegeGPT API is running"}


# Main endpoint
@app.post("/ask")
def ask_question(request: QueryRequest):
    query = request.query

    docs = hybrid_search(query)
    answer = generate_answer(query, docs)

    return {
        "query": query,
        "answer": answer,
        "sources": [
            {
                "text": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs[:3]
        ]
    }