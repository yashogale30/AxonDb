import json
import tempfile
from collections import Counter
from pathlib import Path

from AxonDb.memory import remember
from AxonDb.store import SqliteStore

memories = json.loads((Path(__file__).parent / "demo_memories.json").read_text())
db_path = Path(tempfile.mkdtemp()) / "demo.db"
store = SqliteStore(db_path)

for text in memories:
    remember(store, text)

nodes = store.all_nodes()
edges = store.all_edges()
print("memories:", sum(n.type == "memory" for n in nodes))
print("entities:", sum(n.type != "memory" for n in nodes))
print("edges by type:", dict(Counter(e.rel for e in edges)))
print()

entities = [n for n in nodes if n.type != "memory"]
for n in sorted(entities, key=lambda n: n.name):
    count = sum(1 for e in store.neighbors(n.id) if e.rel == "mentions")
    print(f"{n.name:12} {n.type:12} mentioned in {count} memories")