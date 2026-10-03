# AxonDb

Small, local-first memory storage for durable notes and semantic recall.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
python -m axon.cli add --text "The deployment window is Thursday at 10:00" --tag ops
python -m axon.cli recall "When is the deployment window?"
```

AxonDb stores memories in SQLite and uses a deterministic hashed-token embedding by default, so it works offline with no model download. Optional integrations are exposed through the `api` and `mcp-server` extras.

## Layout

- `src/axon/`: package and adapters
- `tests/`: focused behavior tests
- `demo/`: sample data and walkthrough
- `eval/`: small recall evaluation harness