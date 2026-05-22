import pickle

from ingestion.loader import load_pdf
from ingestion.chunking import split_documents
from ingestion.embedder import create_vectorstore


PDF_PATH = "data/syllabus.pdf"
CHUNKS_PATH = "extracted/chunks.pkl"



def run_pipeline():
    print("Loading PDF...")
    documents = load_pdf(PDF_PATH)

    print("Chunking documents...")
    chunks = split_documents(documents)

    print("Saving chunks...")
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print("Creating vectorstore...")
    create_vectorstore(chunks)

    print("Pipeline complete")


if __name__ == "__main__":
    run_pipeline()