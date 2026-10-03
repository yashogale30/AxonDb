import numpy as np
import pytest

from AxonDb import embed as embed_mod
from AxonDb.models import Node
from AxonDb.resolve import resolve_entity
from AxonDb.store import SqliteStore, vec_to_bytes

# Cosine of atlas and atlas platform is 0.9, atlas and redis is 0.
FAKE = {
    "atlas": [1.0, 0.0, 0.0],
    "atlas platform": [0.9, 0.4359, 0.0],
    "redis": [0.0, 1.0, 0.0],
}


def fake_embed(text):
    return np.array(FAKE[text.strip().lower()], dtype=np.float32)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(embed_mod, "embed", fake_embed)
    s = SqliteStore(tmp_path / "resolve_test.db")
    yield s
    s.conn.close()


def test_creates_new_entity(store):
    node, created = resolve_entity(store, "Atlas", "project")
    assert created is True
    assert node.type == "project"
    assert store.get_node(node.id).name == "Atlas"


def test_exact_match_ignores_case_and_spaces(store):
    first, _ = resolve_entity(store, "Atlas", "project")
    second, created = resolve_entity(store, "  atlas ", "project")
    assert created is False
    assert second.id == first.id


def test_similar_name_reuses_entity(store):
    first, _ = resolve_entity(store, "Atlas", "project")
    second, created = resolve_entity(store, "Atlas Platform", "project")
    assert created is False
    assert second.id == first.id


def test_different_entities_stay_separate(store):
    a, _ = resolve_entity(store, "Atlas", "project")
    r, created = resolve_entity(store, "Redis", "tool")
    assert created is True
    assert r.id != a.id


def test_memory_nodes_are_never_matched(store):
    memory = Node(
        id="", type="memory", name="m1", text="Atlas is a project.",
        embedding=vec_to_bytes(fake_embed("atlas")),
    )
    store.add_node(memory)
    node, created = resolve_entity(store, "Atlas", "project")
    assert created is True
    assert node.id != memory.id