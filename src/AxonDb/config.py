from pathlib import Path

DATA_DIR = Path.home() / ".AxonDb"
DB_PATH = DATA_DIR / "AxonDb.db"

SIMILAR_EDGE_THRESHOLD = 0.80
ENTITY_MERGE_THRESHOLD = 0.85
TOP_K_SEEDS = 4
MAX_HOPS = 2
HOP_DECAY = 0.7

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

LABELS = ["person", "project", "tool", "organization", "preference", "location"]

GLINER_MODEL = "fastino/gliner2-base-v1"
ENTITY_THRESHOLD = 0.4

RELATION_CUES = {
    "leads": ["lead"],
    "uses": ["use"],
    "works_on": ["work", "engineer on"],
    "reports_to": ["report"],
    "deployed_on": ["deploy"],
    "stores_data_in": ["stor"],
    "lives_in": ["live", "based in"],
    "prefers": ["prefer"],
    "tests": ["test"],
    "designs": ["design"],
}
RELATIONS = list(RELATION_CUES)

MAX_FANOUT = 10
RECALL_LIMIT = 8
LINK_ENTITIES = True