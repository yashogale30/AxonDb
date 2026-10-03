import os
import warnings
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException

from .config import DB_PATH
from .recall import recall as recall_memories
from .store import SqliteStore

warnings.filterwarnings("ignore")

app = FastAPI(title="AxonDb")


def _open():
    path = Path(os.environ.get("AXONDB_PATH", DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteStore(path)


@app.get("/graph")
def graph():
    """Every current node and edge, for drawing."""
    store = _open()
    try:
        nodes = [
            {"id": n.id, "type": n.type, "name": n.name, "text": n.text}
            for n in store.all_nodes()
        ]
        edges = [
            {"id": e.id, "src": e.src, "dst": e.dst, "rel": e.rel, "weight": e.weight}
            for e in store.all_edges()
        ]
        return {"nodes": nodes, "edges": edges}
    finally:
        store.conn.close()


@app.get("/recall")
def recall(q: str):
    """The memories that answer a question, plus the path that found them."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="The question is empty.")
    store = _open()
    try:
        result = recall_memories(store, q)
        answers = [{"id": n.id, "text": n.text} for n in result.nodes]
        path = [
            {"src": s.src, "rel": s.rel, "dst": s.dst, "score": round(s.score, 3)}
            for s in result.path
        ]
        return {"answers": answers, "path": path}
    finally:
        store.conn.close()
        
VIEWER_DIR = Path(__file__).resolve().parents[2] / "viewer"
if VIEWER_DIR.is_dir():
    app.mount("/", StaticFiles(directory=VIEWER_DIR, html=True), name="viewer")