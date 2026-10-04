# AxonDb

A fully local graph memory for AI agents. Every answer comes with the path it followed.

TODO 1: put a GIF of the viewer here, showing the path Kiran, tests, Atlas, Postgres lighting up.

## Why

Most agent memory finds sentences that sound like the question. That breaks when the answer sits a step or two away. Take the question "Which database does the project Kiran tests use?" The sentence about Postgres never mentions Kiran. AxonDb stores memories as a graph of people, projects and tools, follows the connections between them, and returns the path so you can see why it gave the answer it did.

## What it does

1. Remember: store a sentence, find the entities in it with a local model, and link it to what is already known.
2. Recall: find the closest memories, follow edges outward, and return the memories plus the path with scores.
3. Forget: close a memory. Nothing is deleted from history.
4. MCP server: works with Claude Desktop and other MCP clients.
5. Viewer: a local web page that draws the graph and highlights the recall path.

Everything runs on your machine. No API keys.

## Example

Question: Which database does the project Kiran tests use?

Path returned: Kiran → tests → Atlas → Postgres sentence

On the demo data, plain vector search ranked the Postgres sentence 8th of 20, while AxonDb returned it with the path above. This is a hand picked demo example, not a benchmark result. Benchmark numbers are below.

## Install (from source, tested on macOS)

```
git clone TODO 2: your repository URL
cd AxonDb
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

The first run downloads two small models (an embedding model and an entity extraction model), so you need internet once. After that it works offline.

## Use with Claude Desktop

Add this to your Claude Desktop config, using your own full paths:

```
{
  "mcpServers": {
    "axondb": {
      "command": "/FULL/PATH/TO/AxonDb/.venv/bin/python",
      "args": ["-m", "AxonDb.mcp_server"],
      "env": { "AXONDB_PATH": "/FULL/PATH/TO/memory.db" }
    }
  }
}
```

TODO 3: replace this block with the exact config that works on your machine.

Tip for agents: the remember tool asks for full sentences with complete names and no pronouns. That gives the entity linker the best chance.

## Command line

```
python -m AxonDb.cli remember "Priya leads the Atlas project."
python -m AxonDb.cli recall "Which project does Priya lead?"
python -m AxonDb.cli list
```

## Viewer

```
python -m uvicorn AxonDb.api:app --port 8000
```

Then open http://127.0.0.1:8000/ in your browser.

## Benchmark

Two sets of 15 hand written questions, each over 30 memory sentences. The answer appears in exactly one sentence, and a hit means the right sentence is among the top 3 or top 5 results. All methods use the same questions and the same embedding model. Questions are one, two or three facts away from the wording of the question.

Development set (used while building, so treat it as optimistic):
1. Vector search: 6 of 15 at top 3, 7 of 15 at top 5.
2. BM25 keywords: 4 of 15, 4 of 15.
3. AxonDb: 4 of 15, 8 of 15.

Held out set (written before any tuning, run on the final code):
1. Vector search: 5 of 15, 6 of 15.
2. BM25 keywords: 3 of 15, 6 of 15.
3. AxonDb: 6 of 15, 9 of 15.

Both sets together (30 questions): at top 5, AxonDb found the answer 17 times against 13 for vector search. At top 3 it was about even (10 against 11).

How to read this: 30 questions is a small sample, so this suggests the graph helps when answers sit a few facts away, and does not prove it. The questions are hand written by one author. The held out set was used once to choose between two candidate versions, so its number is slightly optimistic. Do not compare these numbers with scores published by other memory systems, because they use different models and different metrics.

What did not work: about a dozen tuning variants (more hops, different ranking, different weights) did not clearly beat the simple version. A path aware reranker improved the development set but only tied vector search on the held out set, so it was dropped. Both versions and all results are in `eval/versions` and `eval`.

Reproduce:

```
BENCH=heldout PYTHONPATH=src python eval/run_eval.py
```

## Known limitations

1. Questions that describe a person by role, such as "the designer of the Nova app" or "the intern on Pulse", fail for every method I tested.
2. There is no time handling yet. If a fact changes (someone moves city), both the old and the new fact can be returned.
3. Relative dates such as "last week" are stored as plain text.
4. Graph expansion can add unrelated facts when a question names a popular entity.
5. Entity labels from the extractor are sometimes inconsistent, and extraction mistakes carry into the graph.
6. Some demo questions still fail, for example a question asking for a "cache" when the sentence only says Redis.
7. Tested on macOS with Python 3.14. Expect harmless warnings from the machine learning libraries.

## Privacy

1. All memories are stored in a local SQLite file on your machine. AxonDb sends no memory data anywhere.
2. The embedding and extraction models are downloaded once from Hugging Face on first run.
3. When an agent recalls memories, the returned text goes to whichever model that agent uses. If the agent uses a cloud model, those snippets reach it.
4. To remove everything, delete the database file.

## Roadmap

1. Time handling, so changed facts replace old ones.
2. Better handling of role based questions.
3. A larger benchmark, including a public one.
4. Optional graph database backend.
5. One click install as a Claude Desktop extension.
6. Optional encrypted sync across devices.

## License

MIT