import json
import pickle
import faiss
import numpy as np

from pathlib import Path

from sentence_transformers import SentenceTransformer

from src.parser.detailed_syllabus_parser import (
    detect_detailed_courses,
    split_course_sections
)

from src.chunker.chunker import semantic_chunk


MODEL_NAME = "all-MiniLM-L6-v2"


def build_chunks(text):

    courses = detect_detailed_courses(text)

    all_chunks = []

    for course in courses:

        sections = split_course_sections(course)

        for sec in sections:

            chunks = semantic_chunk(
                sec["content"],
                course_name=course["course_title"],
                section=sec["section"]
            )

            all_chunks.extend(chunks)

    return all_chunks


def generate_embeddings(chunks):

    model = SentenceTransformer(MODEL_NAME)

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    return np.array(embeddings), chunks


def store_faiss(embeddings, chunks):

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    faiss.write_index(
        index,
        "vectorstore/collegegpt.index"
    )

    with open(
        "vectorstore/chunks.pkl",
        "wb"
    ) as f:

        pickle.dump(chunks, f)

    print("FAISS index stored successfully.")


if __name__ == "__main__":

    text = Path(
        "data/extracted_text/syllabus.txt"
    ).read_text(encoding="utf-8")

    chunks = build_chunks(text)

    print(f"Total chunks: {len(chunks)}")

    embeddings, chunks = generate_embeddings(chunks)

    store_faiss(embeddings, chunks)