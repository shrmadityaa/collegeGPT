import pickle
from langchain_community.retrievers import BM25Retriever


CHUNKS_PATH = "extracted/chunks.pkl"


with open(CHUNKS_PATH, "rb") as f:
    chunks = pickle.load(f)


bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 6


def bm25_search(query):
    return bm25_retriever.invoke(query)


def get_all_chunks():
    return chunks