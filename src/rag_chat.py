import ollama

from src.retrieve import CollegeRetriever


SYSTEM_PROMPT = """
You are CollegeGPT, a concise academic assistant.

Answer ONLY from the provided context.

IMPORTANT RULES:
- Keep answers SHORT and DIRECT.
- Do NOT over-explain unless asked.
- For syllabus table questions:
  - Treat L, T, P, and Credits as separate values.
  - NEVER calculate credits manually.
  - Use the credit value exactly as written in the document.

Examples:
L T P Cr
3 0 2 4.0

means:
- Lecture = 3
- Tutorial = 0
- Practical = 2
- Credits = 4.0

NOT 5 credits.

For metadata questions like:
- credits
- semester
- LTP
- course code
- electives

give only the direct answer.

If information truly does not exist,
say:
'I could not find this information in the uploaded documents.'
"""

class CollegeGPT:

    def __init__(self):

        self.retriever = CollegeRetriever()

    def build_prompt(
        self,
        query,
        retrieved_chunks
    ):

        context = "\n\n".join([
            chunk["text"]
            for chunk in retrieved_chunks
        ])

        prompt = f"""
{SYSTEM_PROMPT}

Context:
{context}

Question:
{query}

Give a concise answer:
"""

        return prompt

    def ask(
        self,
        query,
        top_k=8
    ):

        retrieved_chunks = self.retriever.search(
            query,
            top_k=top_k
        )

        prompt = self.build_prompt(
            query,
            retrieved_chunks
        )

        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return {
            "answer": response["message"]["content"],
            "sources": retrieved_chunks
        }


if __name__ == "__main__":

    chatbot = CollegeGPT()

    print("\nCollegeGPT Ready!")
    print("Type 'exit' to quit.\n")

    while True:

        query = input("You: ")

        if query.lower() == "exit":
            break

        result = chatbot.ask(query)

        print("\nCollegeGPT:\n")

        print(result["answer"])

        print("\n" + "="*60 + "\n")