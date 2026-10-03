import time
import uuid
from abc import ABC, abstractmethod

import numpy as np

from .db import connect
from .models import Edge, Node


def new_id():
    return uuid.uuid4().hex


def vec_to_bytes(vec):
    return np.asarray(vec, dtype=np.float32).tobytes()


def bytes_to_vec(data):
    return np.frombuffer(data, dtype=np.float32)


class Store(ABC):
    """The contract. Any backend (SQLite now, a graph database later) implements this."""

    @abstractmethod
    def add_node(self, node): ...

    @abstractmethod
    def get_node(self, node_id): ...

    @abstractmethod
    def find_entity(self, name): ...

    @abstractmethod
    def add_edge(self, edge): ...

    @abstractmethod
    def neighbors(self, node_id): ...

    @abstractmethod
    def all_embeddings(self, types=None): ...

    @abstractmethod
    def close_edge(self, edge_id): ...

    @abstractmethod
    def close_node(self, node_id): ...

    @abstractmethod
    def all_nodes(self): ...

    @abstractmethod
    def all_edges(self): ...

    @abstractmethod
    def set_type(self, node_id, node_type): ...


class SqliteStore(Store):
    def __init__(self, path=None):
        self.conn = connect(path)

    def _node(self, row):
        return Node(**dict(row))

    def _edge(self, row):
        return Edge(**dict(row))

    def add_node(self, node):
        now = time.time()
        if not node.id:
            node.id = new_id()
        if not node.created_at:
            node.created_at = now
        if not node.valid_from:
            node.valid_from = now
        self.conn.execute(
            "INSERT INTO nodes (id, type, name, text, embedding, created_at, "
            "valid_from, valid_to, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (node.id, node.type, node.name, node.text, node.embedding,
             node.created_at, node.valid_from, node.valid_to, node.source),
        )
        self.conn.commit()
        return node

    def get_node(self, node_id):
        row = self.conn.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
        return self._node(row) if row else None

    def find_entity(self, name):
        """Exact match on name, ignoring case and spaces, entities only."""
        row = self.conn.execute(
            "SELECT * FROM nodes WHERE type != 'memory' AND valid_to IS NULL "
            "AND LOWER(TRIM(name)) = ?",
            (name.strip().lower(),),
        ).fetchone()
        return self._node(row) if row else None

    def add_edge(self, edge):
        now = time.time()
        if not edge.id:
            edge.id = new_id()
        if not edge.created_at:
            edge.created_at = now
        if not edge.valid_from:
            edge.valid_from = now
        self.conn.execute(
            "INSERT INTO edges (id, src, dst, rel, weight, created_at, "
            "valid_from, valid_to, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (edge.id, edge.src, edge.dst, edge.rel, edge.weight,
             edge.created_at, edge.valid_from, edge.valid_to, edge.source),
        )
        self.conn.commit()
        return edge

    def neighbors(self, node_id):
        """Current edges touching this node, in either direction."""
        rows = self.conn.execute(
            "SELECT * FROM edges WHERE (src = ? OR dst = ?) AND valid_to IS NULL",
            (node_id, node_id),
        ).fetchall()
        return [self._edge(r) for r in rows]

    def all_embeddings(self, types=None):
        sql = ("SELECT id, embedding FROM nodes "
               "WHERE embedding IS NOT NULL AND valid_to IS NULL")
        params = []
        if types:
            marks = ", ".join("?" for _ in types)
            sql += " AND type IN (" + marks + ")"
            params = list(types)
        rows = self.conn.execute(sql, params).fetchall()
        if not rows:
            return [], np.zeros((0, 0), dtype=np.float32)
        ids = [r["id"] for r in rows]
        matrix = np.vstack([bytes_to_vec(r["embedding"]) for r in rows])
        return ids, matrix

    def close_edge(self, edge_id):
        self.conn.execute(
            "UPDATE edges SET valid_to = ? WHERE id = ?", (time.time(), edge_id)
        )
        self.conn.commit()

    def close_node(self, node_id):
        now = time.time()
        self.conn.execute(
            "UPDATE nodes SET valid_to = ? WHERE id = ?", (now, node_id)
        )
        self.conn.execute(
            "UPDATE edges SET valid_to = ? WHERE (src = ? OR dst = ?) "
            "AND valid_to IS NULL",
            (now, node_id, node_id),
        )
        self.conn.commit()

    def all_nodes(self):
        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE valid_to IS NULL"
        ).fetchall()
        return [self._node(r) for r in rows]

    def all_edges(self):
        rows = self.conn.execute(
            "SELECT * FROM edges WHERE valid_to IS NULL"
        ).fetchall()
        return [self._edge(r) for r in rows]

    def set_type(self, node_id, node_type):
        self.conn.execute(
            "UPDATE nodes SET type = ? WHERE id = ?", (node_type, node_id)
        )
        self.conn.commit()