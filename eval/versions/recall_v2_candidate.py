import re

import numpy as np

from . import embed as embed_mod
from .config import (HOP_DECAY, LINK_ENTITIES, MAX_FANOUT, MAX_HOPS,
                     RECALL_LIMIT, TOP_K_SEEDS)
from .models import PathStep, RecallResult

# An entity named in the question is a certain match, so it starts at full score.
LINKED_SCORE = 1.0


def _short(node, width=60):
    text = node.text if node.type == "memory" else node.name
    return text if len(text) <= width else text[: width - 3] + "..."


def _linked_entities(store, query):
    """Entities whose name appears in the question, matched on whole words."""
    low = query.lower()
    found = []
    for node in store.all_nodes():
        if node.type == "memory":
            continue
        pattern = r"\b" + re.escape(node.name.lower()) + r"\b"
        if re.search(pattern, low):
            found.append(node)
    return found


def recall(store, query, limit=None, k=None):
    """Find the memories that answer a question, and the path that led to them.

    Step 1: start from the memories closest in meaning to the query, and from
            any entity named in the query.
    Step 2: spread outward along edges, losing a bit of score at each hop.
    Step 3: return direct matches and connected memories, half the slots each.
    """
    limit = RECALL_LIMIT if limit is None else limit
    k = TOP_K_SEEDS if k is None else k

    query = " ".join(query.split())
    if not query:
        raise ValueError("Cannot recall with an empty query.")

    all_ids, all_matrix = store.all_embeddings()
    memory_ids, _ = store.all_embeddings(types=["memory"])
    if not memory_ids:
        return RecallResult()

    qvec = embed_mod.embed_query(query)
    scores = embed_mod.similarities(qvec, all_matrix)
    sims = {node_id: float(s) for node_id, s in zip(all_ids, scores)}

    memory_set = set(memory_ids)
    memory_seeds = [
        node_id
        for node_id in sorted(memory_set, key=lambda i: sims[i], reverse=True)
        if sims[node_id] > 0
    ][:k]
    entity_seeds = []
    if LINK_ENTITIES:
        entity_seeds = [n.id for n in _linked_entities(store, query)]
    seed_set = set(memory_seeds) | set(entity_seeds)

    # reached maps a node id to (score, the step that reached it, edge depth)
    reached = {}
    for seed in memory_seeds:
        step = PathStep("query", "seed", seed, sims[seed])
        reached[seed] = (sims[seed], step, 0)
    for seed in entity_seeds:
        step = PathStep("query", "linked", seed, LINKED_SCORE)
        reached[seed] = (LINKED_SCORE, step, 0)

    # When the question names an entity, use it as the graph anchor.  Vector
    # seeds remain direct candidates, but should not start unrelated paths.
    frontier = entity_seeds or memory_seeds
    for _hop in range(MAX_HOPS):
        next_frontier = []
        for node_id in frontier:
            base = reached[node_id][0]
            depth = reached[node_id][2]
            options = []
            for edge in store.neighbors(node_id):
                if edge.rel == "similar_to":
                    continue
                other = edge.dst if edge.src == node_id else edge.src
                options.append((sims.get(other, 0.0), other, edge))
            # Hubs like Atlas have many neighbors. Keep the ones closest to the query.
            options.sort(key=lambda o: o[0], reverse=True)
            for _sim, other, edge in options[:MAX_FANOUT]:
                if other in seed_set:
                    continue
                score = base * HOP_DECAY * edge.weight
                if other not in reached or score > reached[other][0]:
                    step = PathStep(node_id, edge.rel, other, score)
                    reached[other] = (score, step, depth + 1)
                    next_frontier.append(other)
        frontier = next_frontier

    def blended(node_id):
        """Blend endpoint relevance with relevance of its complete evidence path."""
        chain_ids = []
        current = node_id
        visited = set()
        while current in reached and current not in visited:
            visited.add(current)
            if current in memory_set:
                chain_ids.append(current)
            step = reached[current][1]
            if step.src == "query":
                break
            current = step.src
        chain = np.mean([all_matrix[all_ids.index(i)] for i in chain_ids], axis=0)
        path_similarity = float(embed_mod.similarities(qvec, chain[None, :])[0])
        return 0.05 * sims[node_id] + 0.05 * reached[node_id][0] + 0.9 * path_similarity

    ranked = sorted(
        (i for i in reached if i in memory_set),
        key=blended,
        reverse=True,
    )[:limit]

    nodes = []
    path = []
    seen_steps = set()
    for memory_id in ranked:
        node = store.get_node(memory_id)
        if node is None:
            continue
        nodes.append(node)

        chain = []
        current = memory_id
        visited = set()
        while current in reached and current not in visited:
            visited.add(current)
            step = reached[current][1]
            chain.append(step)
            if step.src == "query":
                break
            current = step.src
        for step in reversed(chain):
            key = (step.src, step.rel, step.dst)
            if key not in seen_steps:
                seen_steps.add(key)
                path.append(step)

    for entity_id in entity_seeds:
        step = reached[entity_id][1]
        key = (step.src, step.rel, step.dst)
        if key not in seen_steps:
            seen_steps.add(key)
            path.insert(0, step)

    return RecallResult(nodes=nodes, path=path)


def format_path(store, result):
    """Turn a result into readable lines. This is the explanation."""

    def label(node_id):
        if node_id == "query":
            return "query"
        node = store.get_node(node_id)
        return _short(node) if node else node_id

    lines = []
    for step in result.path:
        lines.append(
            f"{label(step.src)}  →[{step.rel} {step.score:.2f}]→  {label(step.dst)}"
        )
    return lines
