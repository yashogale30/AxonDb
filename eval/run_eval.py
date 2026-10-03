import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from axon.db import AxonDB
from axon.recall import recall

root = Path(__file__).parents[1]
db = AxonDB(":memory:")
for item in json.loads((root / "demo/demo_memories.json").read_text()):
    db.add(item["content"], item.get("tags", []))
questions = json.loads((root / "eval/questions.json").read_text())
results = []
for item in questions:
    matches = recall(db, item["question"], 1)
    hit = bool(matches and item["expected"].lower() in matches[0].content.lower())
    results.append({**item, "answer": matches[0].content if matches else None, "hit": hit})
print(json.dumps(results, indent=2))
