import pickle

from langchain_community.retrievers import BM25Retriever


with open("extracted/chunks.pkl", "rb") as f:
    chunks = pickle.load(f)


bm25_retriever = BM25Retriever.from_documents(chunks)

bm25_retriever.k = 5



def bm25_search(query):
    docs = bm25_retriever.invoke(query)

    return docs