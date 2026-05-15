import re
import uuid

def semantic_chunk(text, course_name=None, section=None, semester=None, chunk_size=500):
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks, current = [], []

    for sent in sentences:
        current.append(sent)
        if sum(len(s) for s in current) > chunk_size:
            chunk_text = " ".join(current).strip()
            chunks.append({
                "id": str(uuid.uuid4()),
                "course": course_name,
                "section": section,
                "semester": semester,
                "text": chunk_text
            })
            current = []
    if current:
        chunks.append({
            "id": str(uuid.uuid4()),
            "course": course_name,
            "section": section,
            "semester": semester,
            "text": " ".join(current).strip()
        })
    return chunks
