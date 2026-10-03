import numpy as np

from . import embed as embed_mod
from .config import ENTITY_MERGE_THRESHOLD, LABELS
from .models import Node
from .store import vec_to_bytes


def clean_name(name):
    """Collapse stray spaces so ' Atlas  ' and 'Atlas' are the same."""
    return " ".join(name.split())


def find_match(store, name, vec):
    """Return (existing_node_or_None, score).

    Stage 1: exact match ignoring case. Stage 2: embedding similarity.
    """
    exact = store.find_entity(name)
    if exact is not None:
        return exact, 1.0

    ids, matrix = store.all_embeddings(types=LABELS)
    if not ids:
        return None, 0.0

    scores = embed_mod.similarities(vec, matrix)
    best = int(np.argmax(scores))
    best_score = float(scores[best])
    if best_score >= ENTITY_MERGE_THRESHOLD:
        return store.get_node(ids[best]), best_score
    return None, best_score


def resolve_entity(store, name, label, source=""):
    """Reuse an existing entity or create a new one.

    Returns (node, created) where created is True only for a new node.
    """
    name = clean_name(name)
    vec = embed_mod.embed(name)

    node, _score = find_match(store, name, vec)
    if node is not None:
        return node, False

    node = Node(
        id="",
        type=label,
        name=name,
        embedding=vec_to_bytes(vec),
        source=source,
    )
    store.add_node(node)
    return node, True