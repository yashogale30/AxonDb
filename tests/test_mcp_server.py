import numpy as np
import pytest

from AxonDb import embed as embed_mod
from AxonDb import mcp_server
from AxonDb import memory as memory_mod

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


@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("AXONDB_PATH", str(tmp_path / "mcp_test.db"))
    monkeypatch.setattr(embed_mod, "embed", fake_embed)
    monkeypatch.setattr(embed_mod, "embed_query", fake_embed)
    monkeypatch.setattr(memory_mod, "extract", fake_extract)


def test_remember_then_recall_returns_answers_and_path():
    assert mcp_server.remember(M1).startswith("Remembered")
    mcp_server.remember(M2)
    out = mcp_server.recall(QUERY)
    assert M2 in out
    assert "Path:" in out
    assert "linked" in out


def test_remembering_twice_says_already_remembered():
    mcp_server.remember(M1)
    assert mcp_server.remember(M1).startswith("Already remembered")


def test_forget_removes_the_memory():
    out = mcp_server.remember(M1)
    short = out.split("[")[1].split("]")[0]
    assert mcp_server.forget(short).startswith("Forgot")
    assert mcp_server.recall(QUERY) == "Nothing remembered yet."
    assert mcp_server.forget(short).startswith("No current memory")