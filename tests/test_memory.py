import numpy as np
import pytest

from AxonDb import embed as embed_mod
from AxonDb import memory as memory_mod
from AxonDb.memory import forget, remember
from AxonDb.store import SqliteStore

M1 = "Priya leads the Atlas project."
M2 = "Atlas stores data in Redis."
M3 = "Rahul likes jazz."


def unit(*pairs):
    vec = np.zeros(7, dtype=np.float32)
    for index, value in pairs:
        vec[index] = value
    return vec


# Entities are orthogonal. M1 and M2 have cosine 0.9, M3 is unrelated to both.
VECTORS = {
    "priya": unit((0, 1.0)),
    "atlas": unit((1, 1.0)),
    "redis": unit((2, 1.0)),
    "rahul": unit((3, 1.0)),
    M1.lower(): unit((4, 1.0)),
    M2.lower(): unit((4, 0.9), (5, 0.4359)),
    M3.lower(): unit((6, 1.0)),
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
    monkeypatch.setattr(memory_mod, "extract", fake_extract)
    s = SqliteStore(tmp_path / "memory_test.db")
    yield s
    s.conn.close()


def test_remember_creates_memory_entities_and_edges(store):
    result = remember(store, M1)
    assert len(store.all_nodes()) == 3
    assert len(store.all_edges()) == 3
    assert result["relations"] == 1
    assert {e.name for e in result["entities"]} == {"Priya", "Atlas"}


def test_shared_entity_connects_memories(store):
    first = remember(store, M1)["memory"]
    second = remember(store, M2)["memory"]
    atlas = [n for n in store.all_nodes() if n.name == "Atlas"]
    assert len(atlas) == 1
    mentioners = {
        e.src for e in store.neighbors(atlas[0].id) if e.rel == "mentions"
    }
    assert mentioners == {first.id, second.id}


def test_similar_memories_are_linked(store):
    remember(store, M1)
    remember(store, M2)
    remember(store, M3)
    similar = [e for e in store.all_edges() if e.rel == "similar_to"]
    assert len(similar) == 1
    assert similar[0].weight == pytest.approx(0.9, abs=0.01)


def test_relation_edges_are_not_duplicated(store):
    remember(store, M1)
    remember(store, M1)
    leads = [e for e in store.all_edges() if e.rel == "leads"]
    assert len(leads) == 1
    names = [n.name for n in store.all_nodes() if n.type != "memory"]
    assert sorted(names) == ["Atlas", "Priya"]


def test_forget_closes_memory_and_its_edges(store):
    memory = remember(store, M1)["memory"]
    assert forget(store, memory.id) is True
    assert store.get_node(memory.id).valid_to is not None
    assert all(n.id != memory.id for n in store.all_nodes())
    assert store.all_edges() == []
    assert forget(store, memory.id) is False


def test_forget_ignores_entities(store):
    result = remember(store, M1)
    entity = result["entities"][0]
    assert forget(store, entity.id) is False

def test_remembering_same_sentence_twice_does_not_duplicate(store):
    first = remember(store, M1)
    second = remember(store, M1)
    assert second["duplicate"] is True
    assert second["memory"].id == first["memory"].id
    memories = [n for n in store.all_nodes() if n.type == "memory"]
    assert len(memories) == 1