from src.retrieve import CollegeRetriever

retriever = CollegeRetriever()

query = "What is pumping lemma?"

results = retriever.search(query)

for i, result in enumerate(results, start=1):

    print(f"\nRESULT {i}")
    print("=" * 60)

    print("COURSE:", result.get("course"))
    print("SECTION:", result.get("section"))

    print("\nTEXT:\n")

    print(result.get("text"))