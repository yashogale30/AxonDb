import json
from pathlib import Path

from AxonDb.extract import extract, raw_extract

memories = json.loads((Path(__file__).parent / "demo_memories.json").read_text())

print("RAW OUTPUT FOR THE FIRST SENTENCE")
print(raw_extract(memories[0]))
print()

for m in memories:
    out = extract(m)
    print(m)
    print("   entities: ", out["entities"])
    print("   relations:", out["relations"])