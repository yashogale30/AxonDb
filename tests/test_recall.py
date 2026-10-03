import numpy as np
import pytest

from AxonDb import embed as embed_mod
from AxonDb import memory as memory_mod
from AxonDb import recall as recall_mod
from AxonDb.memory import forget, remember
from AxonDb.recall import format_path, recall
from AxonDb.store import SqliteStore

M1 = "Priya leads the Atlas project."
M2 = "Atlas stores data in Redis."
M3 = "Rahul likes jazz."
QUERY = "Where does the project Priya leads keep its data?"
QUERY2 = "What does Priya's project use?"
QUERY3 = "Tell me about jazz."


def unit(index):
    vec = np.zeros(8, dtype=np.float32)
    vec[index] = 1.0
    return vec


# Every vector is orthogonal. QUERY points the same way as M1.
# QUERY2 and QUERY3 point the same way as M3, so vectors alone would miss M1 and M2.
VECTORS = {
    "priya": unit(0),
    "atlas": unit(1),
    "redis": unit(2),
    "rahul": unit(3),
    M1.lower(): unit(4),
    M2.lower(): unit(5),
    M3.lower(): unit(6),
    QUERY.lower(): unit(4),
    QUERY2.lower(): unit(6),
    QUERY3.lower(): unit(6),
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
    M3: {"entities": [("Rahul", "person")], "relations": []},
}


def fake_embed(text):
    return VECTORS[text.strip().lower()]


def fake_extract(text):
    return EXTRACTED[text]


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(embed_mod, "embed", fake_embed)
    monkeypatch.setattr(embed_mod, "embed_query", fake_embed)
    monkeypatch.setattr(memory_mod, "extract", fake_extract)
    # Off by default so most tests check the vector side on its own.
    monkeypatch.setattr(recall_mod, "LINK_ENTITIES", False)
    s = SqliteStore(tmp_path / "recall_test.db")
    yield s
    s.conn.close()


@pytest.fixture
def filled(store):
    ids = {}
    for text in (M1, M2, M3):
        ids[text] = remember(store, text)["memory"].id
    return store, ids


def test_two_hop_finds_memory_through_shared_entity(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    result = recall(store, QUERY)
    found = [n.id for n in result.nodes]
    assert found == [ids[M1], ids[M2]]
    assert ids[M3] not in found


def test_path_explains_each_hop(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    result = recall(store, QUERY)
    rels = [s.rel for s in result.path]
    assert rels == ["seed", "mentions", "mentions"]
    scores = [s.score for s in result.path]
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(0.7)
    assert scores[2] == pytest.approx(0.49)


def test_hop_limit_is_respected(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    monkeypatch.setattr(recall_mod, "MAX_HOPS", 1)
    result = recall(store, QUERY)
    assert [n.id for n in result.nodes] == [ids[M1]]


def test_empty_store_returns_nothing(store):
    result = recall(store, QUERY)
    assert result.nodes == []
    assert result.path == []


def test_forgotten_memory_is_not_returned(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    forget(store, ids[M2])
    result = recall(store, QUERY)
    assert [n.id for n in result.nodes] == [ids[M1]]


def test_format_path_uses_readable_names(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    lines = format_path(store, recall(store, QUERY))
    assert lines[0].startswith("query")
    assert any("Atlas" in line for line in lines)
    assert any("Redis" in line for line in lines)


def test_entity_in_query_reaches_memories_vectors_miss(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    monkeypatch.setattr(recall_mod, "LINK_ENTITIES", True)
    result = recall(store, QUERY2)
    found = [n.id for n in result.nodes]
    assert found[0] == ids[M3]
    assert ids[M1] in found
    assert ids[M2] in found
    assert "linked" in [s.rel for s in result.path]


def test_no_entity_in_query_means_no_linked_steps(filled, monkeypatch):
    store, ids = filled
    monkeypatch.setattr(recall_mod, "TOP_K_SEEDS", 1)
    monkeypatch.setattr(recall_mod, "LINK_ENTITIES", True)
    result = recall(store, QUERY3)
    assert all(s.rel != "linked" for s in result.path)