import json
import tempfile
from pathlib import Path

from AxonDb.memory import remember
from AxonDb.recall import format_path, recall
from AxonDb.store import SqliteStore

here = Path(__file__).parent
memories = json.loads((here / "demo_memories.json").read_text())
questions = json.loads((here / "demo_questions.json").read_text())

store = SqliteStore(Path(tempfile.mkdtemp()) / "demo.db")
for text in memories:
    remember(store, text)

for item in questions:
    question = item["question"] if isinstance(item, dict) else item
    result = recall(store, question)
    print("=" * 70)
    print("Q:", question)
    for node in result.nodes:
        print("   *", node.text)
    print("   path:")
    for line in format_path(store, result):
        print("     ", line)