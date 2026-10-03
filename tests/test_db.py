from AxonDb.db import connect


def test_tables_created(tmp_path):
    conn = connect(tmp_path / "test.db")
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r["name"] for r in rows}
    assert "nodes" in names
    assert "edges" in names


def test_wal_mode(tmp_path):
    conn = connect(tmp_path / "test.db")
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"