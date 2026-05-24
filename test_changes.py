import ollama

# ---------------------------------------------------------
# SETUP: Import your current configurations
# ---------------------------------------------------------
# Note: Ensure you have updated llm/prompts.py and llm/generator.py 
# with the new changes before running this to see the final results!
from llm.prompts import SYSTEM_PROMPT
from llm.generator import generate_answer

# We use a dummy Document class to mimic LangChain's structure
class DummyDoc:
    def __init__(self, content):
        self.page_content = content

print("\n" + "="*50)
print("🧪 COLLEGEGPT IMPROVEMENT TESTS")
print("="*50 + "\n")


# ---------------------------------------------------------
# TEST 1: The Context Truncation Fix (The 1200 Char Limit)
# ---------------------------------------------------------
print("▶️ TEST 1: Context Truncation")
# We create a document where the answer is intentionally placed AFTER 1200 characters.
filler = "General syllabus guidelines and generic text. " * 30 # Creates ~1300+ characters of filler
hidden_fact = "CRITICAL FACT: The total credits for the Semester 4 Cloud Computing course is 4 credits."
long_document = filler + hidden_fact

query_1 = "How many credits is the Cloud Computing course in Semester 4?"
docs_1 = [DummyDoc(long_document)]

print(f"Question: {query_1}")
answer_1 = generate_answer(query_1, docs_1)
print(f"Answer:\n{answer_1}\n")
# EXPECTED: 
# Without fix 1: "The syllabus does not contain this information" (because it got cut off).
# With fix 1: "The Cloud Computing course in Semester 4 is 4 credits."


# ---------------------------------------------------------
# TEST 2: Temperature & Determinism Lock
# ---------------------------------------------------------
print("▶️ TEST 2: Determinism (Temperature = 0.0)")
query_2 = "What are the subjects in Semester 4?"
docs_2 = [DummyDoc("Semester 4 subjects include OS, DBMS, and CN.")]

print("Running the exact same query 3 times...")
answers = []
for i in range(3):
    ans = generate_answer(query_2, docs_2).strip()
    answers.append(ans)
    print(f"Run {i+1}: {ans}")

if answers[0] == answers[1] == answers[2]:
    print("✅ Result: SUCCESS. All 3 outputs are 100% identical. The model is locked down.")
else:
    print("❌ Result: FAILED. The outputs changed. Temperature is not set to 0.0.")
print("\n")


# ---------------------------------------------------------
# TEST 3: System Prompt Strictness (Out-of-Scope rejection)
# ---------------------------------------------------------
print("▶️ TEST 3: Strictness and Out-of-Scope Rejection")
query_3 = "Can you write a python script to reverse an array?"
docs_3 = [DummyDoc("Syllabus covers data structures, arrays, linked lists, and trees.")]

print(f"Question: {query_3}")
answer_3 = generate_answer(query_3, docs_3)
print(f"Answer:\n{answer_3}\n")
# EXPECTED: 
# Without fix 3: The LLM might actually try to write the Python code.
# With fix 3: "The syllabus does not contain this information."