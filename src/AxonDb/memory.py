import numpy as np

from . import embed as embed_mod
from .config import SIMILAR_EDGE_THRESHOLD
from .extract import extract
from .models import Edge, Node
from .resolve import resolve_entity
from .store import vec_to_bytes

MAX_SIMILAR = 5


def _clean(text):
    return " ".join(text.split())


def _similar_memories(store, vec):
    """Existing memories close in meaning to this one, best first."""
    ids, matrix = store.all_embeddings(types=["memory"])
    if not ids:
        return []
    scores = embed_mod.similarities(vec, matrix)
    order = np.argsort(-scores)[:MAX_SIMILAR]
    return [
        (ids[i], float(scores[i]))
        for i in order
        if scores[i] >= SIMILAR_EDGE_THRESHOLD
    ]


def _has_edge(store, src, dst, rel):
    for edge in store.neighbors(src):
        if edge.src == src and edge.dst == dst and edge.rel == rel:
            return True
    return False


def remember(store, text, source=""):
    """Store one sentence and wire it into the graph."""
    text = _clean(text)
    if not text:
        raise ValueError("Cannot remember an empty sentence.")

    vec = embed_mod.embed(text)
    # Look for similar memories before adding this one, so it cannot match itself.
    similar = _similar_memories(store, vec)

    memory = store.add_node(
        Node(
            id="",
            type="memory",
            name=text[:80],
            text=text,
            embedding=vec_to_bytes(vec),
            source=source,
        )
    )

    found = extract(text)

    entities = {}
    for name, label in found["entities"]:
        node, _created = resolve_entity(store, name, label, source=memory.id)
        entities[name.lower()] = node

    unique = {}
    for node in entities.values():
        unique[node.id] = node
    for node in unique.values():
        store.add_edge(
            Edge(id="", src=memory.id, dst=node.id, rel="mentions", source=memory.id)
        )

    relation_count = 0
    for head, rel, tail in found["relations"]:
        head_node = entities.get(head.lower())
        tail_node = entities.get(tail.lower())
        if head_node is None or tail_node is None or head_node.id == tail_node.id:
            continue
        if _has_edge(store, head_node.id, tail_node.id, rel):
            continue
        store.add_edge(
            Edge(id="", src=head_node.id, dst=tail_node.id, rel=rel, source=memory.id)
        )
        relation_count += 1

    for other_id, score in similar:
        store.add_edge(
            Edge(
                id="",
                src=memory.id,
                dst=other_id,
                rel="similar_to",
                weight=score,
                source=memory.id,
            )
        )

    return {
        "memory": memory,
        "entities": list(unique.values()),
        "relations": relation_count,
        "similar": len(similar),
    }


def forget(store, memory_id):
    """Close a memory and everything it created. Nothing is deleted."""
    node = store.get_node(memory_id)
    if node is None or node.type != "memory" or node.valid_to is not None:
        return False
    store.close_node(memory_id)
    for edge in store.all_edges():
        if edge.source == memory_id:
            store.close_edge(edge.id)
    return True