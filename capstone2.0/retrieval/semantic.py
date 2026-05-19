from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)


vectorstore = FAISS.load_local(
    "vectorstore/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)



def semantic_search(query, k=5):
    docs = vectorstore.similarity_search(query, k=k)

    return docs