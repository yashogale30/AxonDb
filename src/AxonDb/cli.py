import argparse
import json
import sys
import warnings
from pathlib import Path

from .config import DB_PATH
from .memory import forget, remember
from .recall import format_path, recall
from .store import SqliteStore

# The model libraries print harmless warnings on newer Python versions.
warnings.filterwarnings("ignore")


def _open(args):
    path = Path(args.db) if args.db else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteStore(path)


def _short(node_id):
    return node_id[:8]


def _memories(store):
    nodes = [n for n in store.all_nodes() if n.type == "memory"]
    return sorted(nodes, key=lambda n: n.created_at)


def cmd_remember(args):
    store = _open(args)
    try:
        result = remember(store, args.text, source="cli")
        memory = result["memory"]
        if result["duplicate"]:
            print(f"Already remembered [{_short(memory.id)}] {memory.text}")
            return 0
        print(f"Remembered [{_short(memory.id)}] {memory.text}")
        names = ", ".join(f"{n.name} ({n.type})" for n in result["entities"])
        print(f"  entities: {names or 'none'}")
        print(
            f"  relations added: {result['relations']}, "
            f"similar memories linked: {result['similar']}"
        )
    finally:
        store.conn.close()
    return 0


def cmd_recall(args):
    store = _open(args)
    try:
        result = recall(store, args.query, limit=args.limit)
        if not result.nodes:
            print("Nothing remembered yet.")
            return 0
        print("Answers:")
        for node in result.nodes:
            print(f"  [{_short(node.id)}] {node.text}")
        print("Path:")
        for line in format_path(store, result):
            print(f"  {line}")
    finally:
        store.conn.close()
    return 0


def cmd_forget(args):
    store = _open(args)
    try:
        matches = [n for n in _memories(store) if n.id.startswith(args.id)]
        if not matches:
            print("No current memory has that id. Try the list command.")
            return 1
        if len(matches) > 1:
            print("That id matches more than one memory. Type more characters.")
            return 1
        memory = matches[0]
        forget(store, memory.id)
        print(f"Forgot [{_short(memory.id)}] {memory.text}")
        print("It is closed, not deleted, so the history is kept.")
    finally:
        store.conn.close()
    return 0


def cmd_list(args):
    store = _open(args)
    try:
        memories = _memories(store)
        if not memories:
            print("No memories.")
            return 0
        for node in memories:
            print(f"[{_short(node.id)}] {node.text}")
    finally:
        store.conn.close()
    return 0


def cmd_load(args):
    sentences = json.loads(Path(args.file).read_text())
    store = _open(args)
    try:
        for text in sentences:
            remember(store, text, source="load")
        print(f"Loaded {len(sentences)} memories.")
    finally:
        store.conn.close()
    return 0


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", help="database file (default: ~/.AxonDb/AxonDb.db)")

    parser = argparse.ArgumentParser(
        prog="axondb", description="Local graph memory for AI agents."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("remember", parents=[common], help="store one sentence")
    p.add_argument("text")
    p.set_defaults(func=cmd_remember)

    p = sub.add_parser("recall", parents=[common], help="ask a question")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=None)
    p.set_defaults(func=cmd_recall)

    p = sub.add_parser("forget", parents=[common], help="close a memory by id")
    p.add_argument("id")
    p.set_defaults(func=cmd_forget)

    p = sub.add_parser("list", parents=[common], help="show current memories")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("load", parents=[common], help="remember every sentence in a JSON file")
    p.add_argument("file")
    p.set_defaults(func=cmd_load)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())