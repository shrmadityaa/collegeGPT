from pathlib import Path
from src.parser.table_parser import table_to_sentences

text = Path(
    "data/extracted_text/syllabus.txt"
).read_text(encoding="utf-8")

results = table_to_sentences(text)

print(f"Total parsed courses: {len(results)}")
print()

for r in results[:10]:
    print(r)
    print()