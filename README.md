# AxonDb

A fully local graph memory for AI agents. Every answer comes with the path it followed.

TODO 1: put a GIF here showing the viewer lighting up the path Kiran, tests, Atlas, Postgres.

## Contents

1. Why AxonDb
2. Features
3. Quick start
4. How it works
5. Benchmark
6. Known limitations
7. Privacy
8. Project layout
9. Development
10. Roadmap
11. License

## 1. Why AxonDb

Most agent memory works by finding stored sentences that sound like the question. That breaks when the answer sits a step or two away from the wording of the question.

Take this question: "Which database does the project Kiran tests use?" The sentence that holds the answer, "Atlas stores its bookings in Postgres.", never mentions Kiran. A similarity search has no reason to rank it highly. AxonDb stores memories as a graph of people, projects and tools. It finds Kiran, follows the connection to Atlas, then finds the Postgres sentence, and it returns that path so you can see exactly why it gave the answer it did.

Three ideas drive the design:

1. Local. Memories live in one SQLite file on your machine. No account, no API key, no cloud.
2. Connected. Sentences that mention the same entity are linked, so facts that belong together can be found together.
3. Explainable. Recall returns the real path it traversed, with a score on every step, not a story written afterward.

## 2. Features

1. Remember, recall and forget, from the command line or from an agent.
2. An MCP server, so Claude Desktop and other MCP clients can use it as memory.
3. A local web viewer that draws the graph and highlights the path of the last recall.
4. Entity and relation extraction with a small local model.
5. Nothing is ever deleted. Forgotten memories are closed with an end timestamp, so history stays intact.
6. A storage interface, so SQLite can be replaced by another backend later.

## 3. Quick start

Developed and tested on macOS with Python 3.14.

### Install from source

```
git clone TODO 2: your repository URL
cd AxonDb
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

The first run downloads two small models from Hugging Face, an embedding model and an entity extraction model. You need internet once. After that everything works offline.

### Two ways to start

Option A: try the demo (separate database, your real memory is untouched)

```
AxonDb load demo/demo_memories.json --db demo.db
AxonDb list --db demo.db
AxonDb recall "Which database does the project Kiran tests use?" --db demo.db
```

This creates a file called demo.db in the current folder and puts the 20 demo sentences in it. Expected result: the memory "Atlas stores its bookings in Postgres." together with the path Kiran, tests, Atlas, Postgres sentence. Delete demo.db whenever you like.

Option B: start fresh with your own memory

```
AxonDb remember "Priya leads the Atlas project."
AxonDb remember "Atlas uses Redis for seat locking."
AxonDb recall "Which project does Priya lead?"
```

Without the database option, memories go to the default database at ~/.AxonDb/AxonDb.db. Do not load the demo data into it.

To start over at any time, delete the database file you were using.

TODO 3: run both options yourself and fix the syntax here if any command differs.

Expected result: the memory "Atlas stores its bookings in Postgres." together with the path Kiran, tests, Atlas, Postgres sentence.

### Use it from Claude Desktop

Open the Claude Desktop config file. On macOS it is at:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add this, with your own full paths, then restart Claude Desktop:

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

TODO 4: replace this block with the exact config that works on your machine.

The server gives the agent three tools: remember, recall and forget. The remember tool asks the agent to write complete sentences with full names and no pronouns, because that gives the entity linker the best chance of connecting facts.

### Open the viewer

```
AXONDB_PATH=/FULL/PATH/TO/memory.db python -m uvicorn AxonDb.api:app --port 8000
```

Then open http://127.0.0.1:8000/ in your browser. The page draws the graph, and after a recall it highlights the path that was followed.

## 4. How it works

### Remember

When a sentence arrives:

1. It is stored as a memory node. An exact duplicate of an existing memory is ignored.
2. It is turned into a vector with the BGE small English v1.5 embedding model.
3. GLiNER2 extracts entities (person, project, tool, organization, preference, location) and relations (leads, uses, reports to, deployed on and so on). Three cleanup rules follow. A relation is kept only if its trigger word really appears in the sentence. Names like "Atlas project" are snapped to the entity "Atlas". Lowercase multi word phrases are dropped.
4. Each entity is resolved against the graph. An exact match, ignoring case and spaces, reuses the existing node. Otherwise an entity whose name embedding is similar enough, above 0.85, is merged with it. If the extractor typed a name as an organization but a person only relation names it, it is retyped as a person.
5. Edges are created: mentions edges from the memory to each entity, typed relation edges between entities, and similar_to edges between memories whose similarity is above 0.80.

Facts about the same entity end up connected through that shared node. If one sentence says "Priya leads the Atlas project" and another says "Atlas uses Redis", the two share the Atlas node, so Priya and Redis are connected without anyone linking them by hand.

### Recall

When a question arrives:

1. It is embedded with the same model, using the query prefix that BGE models expect.
2. The seeds are the 4 memories closest to the question, plus every entity whose name appears in the question. An entity named in the question starts at a score of 1.0.
3. The search spreads two hops along edges. The score decays by 0.7 per hop and is multiplied by the edge weight. Each node keeps only its 10 neighbors closest to the question, so busy hubs do not flood the results.
4. The result list is split between direct matches and connected memories. Connected memories are ranked by half their own similarity plus half the strength of the path that reached them.
5. The answer is the list of memories plus the path: a list of steps, each with source, relation, destination and score.

Because one fact costs two steps in this graph (entity to memory, then memory to entity), two hops reach one fact beyond the entity named in the question. Longer chains are possible but get weaker.

### Data model

Two SQLite tables, nodes and edges. A node is either a memory or an entity, and entity nodes carry their label as their type. Every node and edge has a valid from and a valid to timestamp. Forgetting sets valid to, and every read ignores closed rows. SQLite runs in WAL mode.

All storage goes through one interface, Store, implemented by SqliteStore. No other file touches SQL.

### Default settings

```
Entity merge threshold        0.85
Similar memory edge threshold 0.80
Seed memories                 4
Hops                          2
Hop decay                     0.7
Neighbors kept per node       10
Results returned              8
```

All of these live in src/AxonDb/config.py.

## 5. Benchmark

### What was tested

A generated set of 100 memories and 100 questions, made by eval/make_big_set.py.

1. The memories describe 10 projects. Each project has a lead, a description, a programming language, a database, a cloud, a tool, and a backend engineer who reports to the lead. Leads and engineers each have a home city. That gives 10 sentences per project.
2. The 100 questions are split by how many facts you must connect. 25 are one hop ("Which database does Kestrel use?"), 45 are two hop ("Which cloud is the project Aarav leads deployed on?") and 30 are three hop ("Which database does the project that Kavya's manager leads use?").
3. Every answer appears in exactly one memory sentence, and the generator checks this with an assertion. A hit means the right sentence was found.
4. The same fact is asked at different depths, so you can see how each method degrades as the chain gets longer. 20 questions refer to people by role, such as "the backend engineer on Quartz".

### Methods compared

1. Vector: cosine similarity with the same BGE model and query prefix that AxonDb uses.
2. BM25: classic keyword search.
3. AxonDb: the recall described above.

Every method gets the same questions, and each is cut to exactly the top 3 or top 5 memories. A question counts as a hit if the answer text appears in one of those memories.

### Results

Number of questions, out of 100, where the answer was found:

```
                        Top 3 results                 Top 5 results
                    Vector   BM25  AxonDb         Vector   BM25  AxonDb
All 100 questions       35     19      46             41     29      63
Percent                35%    19%     46%            41%    29%     63%
```

Split by number of hops:

```
                        Top 3 results                 Top 5 results
                    Vector   BM25  AxonDb         Vector   BM25  AxonDb
1 hop (25)              24     15      25             25     25      25
2 hop (45)               4      2      11              8      2      18
3 hop (30)               7      2      10              8      2      20
```

The same split in percent:

```
                        Top 3 results                 Top 5 results
                    Vector   BM25  AxonDb         Vector   BM25  AxonDb
1 hop                  96%    60%    100%           100%   100%    100%
2 hop                   9%     4%     24%            18%     4%     40%
3 hop                  23%     7%     33%            27%     7%     67%
```

### How to read it

1. One hop questions are a tie at the top 5. Any method can find an answer that sits in one sentence.
2. AxonDb helps most on two and three hop questions. At the top 5 it found the answer for 18 of 45 two hop questions against 8 for vector search, and for 20 of 30 three hop questions against 8.
3. Keyword search is the weakest on multi step questions, because the answer sentence rarely shares words with the question.
4. Overall at the top 5, AxonDb found the answer 63 times, plain vector search 41 times and keyword search 29 times.

### Honest caveats

1. The data is templated and clean. Names are unique, every sentence follows one pattern and every answer appears once. Real conversations are messier, so expect smaller gaps in practice.
2. One author wrote the data and the system. The questions were fixed before the first run, and nothing in AxonDb was tuned on this set, but an independent test would be stronger.
3. 100 questions is still a modest sample. The top 5 gap of 22 questions is large compared with what chance would normally produce. The top 3 gap of 11 questions is suggestive, not conclusive.
4. A hybrid baseline that combines vector and keyword search is common in real systems and was not tested. It would probably score higher than plain vector search, so the fair claim is that AxonDb beats plain vector search and plain keyword search, not that it beats every alternative.
5. Do not compare these numbers with scores published by other memory systems. Their models, data and metrics differ.
6. A hit means the right sentence was returned. It does not test whether an agent then answers correctly.

### Earlier, smaller tests

Before this set, two hand written sets of 15 questions each gave much closer results. On the first, AxonDb found 4 answers in the top 3 against 6 for vector search, and 8 in the top 5 against 7. On the second, which was written before any tuning, AxonDb found 6 in the top 3 against 5 for vector search, and 9 in the top 5 against 6. About a dozen tuning attempts on the first set (more hops, different ranking, different weights) did not clearly improve on the simple version, and a path aware reranker that helped the first set fell back to a tie on the second. The simple version was kept. Those files were removed from this repository to keep it small, and they remain in the git history.

### Reproduce

The benchmark needs one extra package:

```
pip install rank_bm25
python eval/make_big_set.py
PYTHONPATH=src python eval/run_eval.py
```

The generator rebuilds the memories and questions. The runner loads the memories into a temporary database using the real remember pipeline, asks every question three ways, and writes the table to eval/results_big.md. It takes a few minutes, because the extractor processes all 100 sentences.

## 6. Known limitations

1. Questions that refer to someone by role, such as "the designer of the Nova app" or "the intern on Pulse", were a weak spot for every method in earlier tests.
2. There is no time handling yet. If a fact changes, for example someone moves city, both the old and the new fact can be returned.
3. Relative dates such as "last week" are stored as plain text.
4. Graph expansion can add unrelated facts when a question names a busy entity.
5. Entity labels from the extractor are sometimes inconsistent, and extraction mistakes carry into the graph.
6. Matching is on the words in the memory. A question that asks for a "cache" will miss a sentence that only says Redis.
7. Developed on macOS with Python 3.14. Expect harmless warnings from the machine learning libraries.

## 7. Privacy

1. All memories are stored in one local SQLite file. AxonDb sends no memory data anywhere.
2. The embedding and extraction models are downloaded once from Hugging Face on first run, and run locally after that.
3. When an agent recalls memories, the returned text goes to whichever model that agent uses. If the agent uses a cloud model, those snippets reach it. Local storage and search do not change that.
4. To remove everything, delete the database file.

## 8. Project layout

```
src/AxonDb/
    config.py        settings and thresholds
    models.py        Node, Edge, PathStep, RecallResult
    db.py            SQLite connection and schema
    store.py         Store interface and SqliteStore
    embed.py         embedding model
    extract.py       entity and relation extraction
    resolve.py       entity matching
    memory.py        remember and forget
    recall.py        recall and path building
    cli.py           command line tool
    mcp_server.py    MCP server
    api.py           local API for the viewer
    viewer/          web page and d3 library
tests/               46 tests
demo/                20 sentence demo set and recording script
eval/                100 question benchmark, generator and results
```

## 9. Development

```
pip install pytest
python -m pytest
```

All 46 tests should pass. The torch and attention warnings you may see on Python 3.14 are harmless.

## 10. Roadmap

1. Time handling, so a changed fact replaces the old one.
2. Better handling of questions that refer to people by role.
3. A hybrid vector and keyword baseline, and a larger public benchmark.
4. An optional graph database backend behind the Store interface.
5. A one click install as a Claude Desktop extension, and a package on PyPI.
6. Optional encrypted sync across devices.

## 11. License

MIT