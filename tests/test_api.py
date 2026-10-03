import numpy as np
import pytest
from fastapi.testclient import TestClient

from AxonDb import embed as embed_mod
from AxonDb import memory as memory_mod
from AxonDb.api import app
from AxonDb.memory import remember
from AxonDb.store import SqliteStore

M1 = "Priya leads the Atlas project."
M2 = "Atlas stores data in Redis."
QUERY = "Where does the project Priya leads keep its data?"


def unit(index):
    vec = np.zeros(8, dtype=np.float32)
    vec[index] = 1.0
    return vec


VECTORS = {
    "priya": unit(0),
    "atlas": unit(1),
    "redis": unit(2),
    M1.lower(): unit(4),
    M2.lower(): unit(5),
    QUERY.lower(): unit(4),
}

EXTRACTED = {
    M1: {
        "entities": [("Priya", "person"), ("Atlas", "project")],
        "relations": [("Priya", "leads", "Atlas")],
    },
    M2: {
        "entities": [("Atlas", "project"), ("Redis", "tool")],
        "relations": [("Atlas", "stores_data_in", "Redis")],
    },
}


def fake_embed(text):
    return VECTORS[text.strip().lower()]


def fake_extract(text):
    return EXTRACTED[text]


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "api_test.db"
    monkeypatch.setenv("AXONDB_PATH", str(db_path))
    monkeypatch.setattr(embed_mod, "embed", fake_embed)
    monkeypatch.setattr(embed_mod, "embed_query", fake_embed)
    monkeypatch.setattr(memory_mod, "extract", fake_extract)
    store = SqliteStore(db_path)
    remember(store, M1)
    remember(store, M2)
    store.conn.close()
    return TestClient(app)


def test_graph_returns_nodes_and_edges(client):
    data = client.get("/graph").json()
    names = {n["name"] for n in data["nodes"]}
    assert {"Priya", "Atlas", "Redis"} <= names
    rels = {e["rel"] for e in data["edges"]}
    assert {"mentions", "leads", "stores_data_in"} <= rels


def test_recall_returns_answers_and_path(client):
    data = client.get("/recall", params={"q": QUERY}).json()
    assert M2 in [a["text"] for a in data["answers"]]
    assert data["path"][0]["src"] == "query"
    assert "linked" in [s["rel"] for s in data["path"]]


def test_recall_rejects_empty_question(client):
    assert client.get("/recall", params={"q": "  "}).status_code == 400