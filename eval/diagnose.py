import json
from pathlib import Path

from AxonDb.embed import embed_query, similarities
from AxonDb.memory import remember
from AxonDb.recall import format_path, recall
from AxonDb.store import SqliteStore

HERE = Path(__file__).parent
DB = Path("/tmp/axon_bench_dev.db")


def find_rank(answer, texts):
    needle = answer.lower()
    for i, t in enumerate(texts):
        if needle in t.lower():
            return i + 1
    return None


def recall_texts(result, store):
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


def show(rank):
    return str(rank) if rank else "none"


def main():
    memories = json.loads((HERE / "bench_memories.json").read_text())
    questions = json.loads((HERE / "bench_questions.json").read_text())

    first_time = not DB.exists()
    store = SqliteStore(DB)
    if first_time:
        print("Building the database once. This takes a few minutes.")
        for m in memories:
            remember(store, m)

    ids, matrix = store.all_embeddings(types=["memory"])
    texts = [store.get_node(i).text for i in ids]

    top3, low, missing = [], [], []

    for q in questions:
        query = q["question"]
        scores = similarities(embed_query(query), matrix)
        order = sorted(range(len(texts)), key=lambda i: scores[i], reverse=True)
        vec_rank = find_rank(q["answer"], [texts[i] for i in order])

        result = recall(store, query, limit=30)
        graph_rank = find_rank(q["answer"], recall_texts(result, store))

        print(str(q["hops"]) + " hop   vector rank " + show(vec_rank).ljust(5)
              + " graph rank " + show(graph_rank).ljust(5) + " " + query)

        if graph_rank and graph_rank <= 3:
            top3.append(query)
        elif graph_rank:
            low.append(query)
        else:
            missing.append(query)
            print("      path returned:")
            try:
                for line in str(format_path(store, result)).splitlines()[:8]:
                    print("        " + line)
            except Exception as err:
                print("        (could not print path: " + str(err) + ")")

    print()
    print("Graph found the answer in its top 3:", len(top3))
    print("Graph found it but ranked 4th or lower:", len(low))
    print("Graph never retrieved it:", len(missing))


if __name__ == "__main__":
    main()