import json
from pathlib import Path

DEMO = Path(__file__).parent.parent / "demo"


def test_demo_files_load():
    memories = json.loads((DEMO / "demo_memories.json").read_text())
    questions = json.loads((DEMO / "demo_questions.json").read_text())
    assert len(memories) == 20
    assert len(questions) >= 5
    assert all(m.strip().endswith(".") for m in memories)