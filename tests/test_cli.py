import re

import numpy as np
import pytest

from AxonDb import cli
from AxonDb import embed as embed_mod
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


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(embed_mod, "embed", fake_embed)
    monkeypatch.setattr(embed_mod, "embed_query", fake_embed)
    monkeypatch.setattr(memory_mod, "extract", fake_extract)
    return str(tmp_path / "cli_test.db")


def run(*args):
    return cli.main(list(args))


def test_remember_then_recall_prints_answers_and_path(db, capsys):
    assert run("remember", M1, "--db", db) == 0
    assert run("remember", M2, "--db", db) == 0
    capsys.readouterr()
    assert run("recall", QUERY, "--db", db) == 0
    out = capsys.readouterr().out
    assert M2 in out
    assert "Path:" in out
    assert "linked" in out


def test_forget_by_id_prefix(db, capsys):
    run("remember", M1, "--db", db)
    out = capsys.readouterr().out
    short = re.search(r"\[([0-9a-f]{8})\]", out).group(1)
    assert run("forget", short, "--db", db) == 0
    capsys.readouterr()
    run("list", "--db", db)
    assert "No memories" in capsys.readouterr().out


def test_forget_unknown_id_fails(db, capsys):
    assert run("forget", "deadbeef", "--db", db) == 1