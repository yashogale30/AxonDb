from dataclasses import dataclass, field


@dataclass
class Node:
    id: str
    type: str
    name: str
    text: str = ""
    embedding: bytes | None = None
    created_at: float = 0.0
    valid_from: float = 0.0
    valid_to: float | None = None
    source: str = ""


@dataclass
class Edge:
    id: str
    src: str
    dst: str
    rel: str
    weight: float = 1.0
    created_at: float = 0.0
    valid_from: float = 0.0
    valid_to: float | None = None
    source: str = ""


@dataclass
class PathStep:
    src: str
    rel: str
    dst: str
    score: float


@dataclass
class RecallResult:
    nodes: list = field(default_factory=list)
    path: list = field(default_factory=list)