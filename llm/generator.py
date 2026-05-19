import ollama

from llm.prompts import SYSTEM_PROMPT


MODEL_NAME = "phi3:mini"


def generate_answer(query, docs):
    
    # Fix: No more character limits, pass the full context
    context = "\n\n".join([doc.page_content for doc in docs])

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"SYLLABUS CONTEXT:\n{context}\n\nQUESTION:\n{query}\n\nFINAL ANSWER:"
            }
        ],
        options={
            "temperature": 0.0 # Fix: Forces strict, concise, hallucination-free outputs
        }
    )

    return response["message"]["content"]