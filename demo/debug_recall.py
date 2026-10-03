import json
import sys
import tempfile
from pathlib import Path

from AxonDb import embed as embed_mod
from AxonDb.memory import remember
from AxonDb.recall import recall
from AxonDb.store import SqliteStore

here = Path(__file__).parent
memories = json.loads((here / "demo_memories.json").read_text())
questions = json.loads((here / "demo_questions.json").read_text())
only = sys.argv[1].lower() if len(sys.argv) > 1 else ""

store = SqliteStore(Path(tempfile.mkdtemp()) / "debug.db")
for text in memories:
    remember(store, text)

ids, matrix = store.all_embeddings(types=["memory"])

for item in questions:
    question = item["question"] if isinstance(item, dict) else item
    if only and only not in question.lower():
        continue
    returned = {n.id for n in recall(store, question).nodes}
    sims = embed_mod.similarities(embed_mod.embed(question), matrix)
    order = sorted(range(len(ids)), key=lambda i: sims[i], reverse=True)
    print("=" * 70)
    print("Q:", question)
    for rank, i in enumerate(order, start=1):
        node = store.get_node(ids[i])
        flag = "RETURNED" if ids[i] in returned else ""
        print(f"{rank:2}  {sims[i]:.2f}  {flag:9} {node.text}")