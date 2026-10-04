import json
import re
import tempfile
from pathlib import Path

from rank_bm25 import BM25Okapi

from AxonDb.embed import embed_query, similarities
from AxonDb.memory import remember
from AxonDb.recall import recall
from AxonDb.store import SqliteStore

HERE = Path(__file__).parent
KS = (3, 5)
METHODS = ("vector", "bm25", "graph")


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def hit(answer, texts):
    """A success means the answer text appears in one of the returned memories."""
    needle = answer.lower()
    return any(needle in t.lower() for t in texts)


def top(scores, k):
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return order[:k]


def result_texts(result, store):
    """Pull the memory sentences out of whatever recall returned."""
    texts = []
    for item in result.nodes:
        if isinstance(item, (tuple, list)) and item:
            item = item[0]
        if isinstance(item, str):
            item = store.get_node(item)
        if item is None or getattr(item, "type", "memory") != "memory":
            continue
        texts.append(item.text)
    return texts


def summarise(rows, label, lines):
    n = len(rows)
    lines.append(label + " (" + str(n) + " questions)")
    for method in METHODS:
        c3 = sum(1 for r in rows if r[method][3])
        c5 = sum(1 for r in rows if r[method][5])
        lines.append(
            "   " + method.ljust(7) + " k3 " + str(c3) + "/" + str(n)
            + "    k5 " + str(c5) + "/" + str(n)
        )


def main():
    memories = json.loads((HERE / "bench_memories.json").read_text())
    questions = json.loads((HERE / "bench_questions.json").read_text())
    lines = []

    with tempfile.TemporaryDirectory() as tmp:
        store = SqliteStore(Path(tmp) / "bench.db")
        print("Loading", len(memories), "memories. This runs the real extractor, so wait a bit.")
        for m in memories:
            remember(store, m)

        ids, matrix = store.all_embeddings(types=["memory"])
        texts = [store.get_node(i).text for i in ids]
        print("Memories stored:", len(texts))
        assert len(texts) > 0, "No memory nodes found. Check the node type name in memory.py."

        bm25 = BM25Okapi([tokens(t) for t in texts])
        rows = []

        for q in questions:
            query = q["question"]
            vec_scores = similarities(embed_query(query), matrix)
            bm_scores = bm25.get_scores(tokens(query))

            row = {"hops": q["hops"], "vector": {}, "bm25": {}, "graph": {}}
            for k in KS:
                row["vector"][k] = hit(q["answer"], [texts[i] for i in top(vec_scores, k)])
                row["bm25"][k] = hit(q["answer"], [texts[i] for i in top(bm_scores, k)])
                found = result_texts(recall(store, query, limit=k), store)[:k]
                row["graph"][k] = hit(q["answer"], found)
            rows.append(row)

            marks = []
            for method in METHODS:
                for k in KS:
                    marks.append(method[0].upper() + str(k) + ":" + ("Y" if row[method][k] else "n"))
            lines.append(str(q["hops"]) + " hop  " + " ".join(marks) + "  " + query)

        lines.append("")
        summarise(rows, "All questions", lines)
        for h in (1, 2, 3):
            group = [r for r in rows if r["hops"] == h]
            lines.append("")
            summarise(group, str(h) + " hop questions", lines)

    output = "\n".join(lines)
    print()
    print(output)
    (HERE / "results.md").write_text(output + "\n")


if __name__ == "__main__":
    main()