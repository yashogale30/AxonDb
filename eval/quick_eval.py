import json
from pathlib import Path

from AxonDb.embed import embed_query, similarities
from AxonDb.recall import recall
from AxonDb.store import SqliteStore

HERE = Path(__file__).parent
DB = Path("/tmp/axon_bench_dev.db")
KS = (3, 5)


def hit(answer, texts):
    needle = answer.lower()
    return any(needle in t.lower() for t in texts)


def main():
    questions = json.loads((HERE / "bench_questions.json").read_text())
    store = SqliteStore(DB)
    ids, matrix = store.all_embeddings(types=["memory"])
    texts = [store.get_node(i).text for i in ids]

    rows = []
    for q in questions:
        scores = similarities(embed_query(q["question"]), matrix)
        order = sorted(range(len(texts)), key=lambda i: scores[i], reverse=True)
        row = {"hops": q["hops"], "vector": {}, "graph": {}}
        for k in KS:
            row["vector"][k] = hit(q["answer"], [texts[i] for i in order[:k]])
            found = [n.text for n in recall(store, q["question"], limit=k).nodes][:k]
            row["graph"][k] = hit(q["answer"], found)
        rows.append(row)

    def line(label, group):
        n = len(group)
        parts = []
        for method in ("vector", "graph"):
            c3 = sum(1 for r in group if r[method][3])
            c5 = sum(1 for r in group if r[method][5])
            parts.append(method + " k3 " + str(c3) + "/" + str(n) + " k5 " + str(c5) + "/" + str(n))
        print(label.ljust(10) + "   ".join(parts))

    line("all", rows)
    for h in (1, 2, 3):
        line(str(h) + " hop", [r for r in rows if r["hops"] == h])


if __name__ == "__main__":
    main()