import ollama

from llm.prompts import SYSTEM_PROMPT


MODEL_NAME = "phi3:mini"


def generate_answer(query, docs):

    context = "\n\n".join([
        doc.page_content
        for doc in docs
    ])

    prompt = f"""
{SYSTEM_PROMPT}

SYLLABUS CONTEXT:
{context}

QUESTION:
{query}

FINAL ANSWER:
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.0,
            "num_predict": 150 #OPTIONAL: acts as a hard limit on response length
        }
    )

    return response["message"]["content"]