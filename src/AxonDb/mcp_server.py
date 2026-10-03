import contextlib
import os
import sys
import warnings
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import embed as embed_mod
from .config import DB_PATH
from .extract import get_extractor
from .memory import forget as forget_memory
from .memory import remember as remember_memory
from .recall import format_path
from .recall import recall as recall_memories
from .store import SqliteStore

warnings.filterwarnings("ignore")

mcp = FastMCP("AxonDb")


@contextlib.contextmanager
def _quiet():
    """The model libraries print to stdout, which would corrupt the MCP channel."""
    with contextlib.redirect_stdout(sys.stderr):
        yield


def _open():
    path = Path(os.environ.get("AXONDB_PATH", DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteStore(path)


@mcp.tool()
def remember(text: str) -> str:
    """Store one fact in long term memory.

    Write one complete sentence per call, using full names and no pronouns.
    Write "Priya leads the Atlas project." and never "She leads it.", because
    the memory is read later without the conversation around it.
    """
    store = _open()
    try:
        with _quiet():
            result = remember_memory(store, text, source="mcp")
        memory = result["memory"]
        short = memory.id[:8]
        if result["duplicate"]:
            return f"Already remembered [{short}] {memory.text}"
        names = ", ".join(n.name for n in result["entities"]) or "none"
        return f"Remembered [{short}] {memory.text}\nEntities: {names}"
    except ValueError:
        return "Nothing was stored because the sentence was empty."
    finally:
        store.conn.close()


@mcp.tool()
def recall(question: str) -> str:
    """Look up what is remembered that answers a question.

    Returns the matching memories, then the path of links that was followed to
    find them, so the answer can be explained. Ask in a complete sentence and
    use full names, for example "Which database does the project Kiran tests use?"
    """
    store = _open()
    try:
        with _quiet():
            result = recall_memories(store, question)
        if not result.nodes:
            return "Nothing remembered yet."
        lines = ["Answers:"]
        for node in result.nodes:
            lines.append(f"[{node.id[:8]}] {node.text}")
        lines.append("Path:")
        lines.extend(format_path(store, result))
        return "\n".join(lines)
    except ValueError:
        return "Nothing was searched because the question was empty."
    finally:
        store.conn.close()


@mcp.tool()
def forget(memory_id: str) -> str:
    """Forget one memory, using the id shown in square brackets by remember and recall.

    The memory is closed and no longer returned, but its history is kept.
    """
    store = _open()
    try:
        prefix = memory_id.strip()
        if not prefix:
            return "No id was given."
        matches = [
            n for n in store.all_nodes()
            if n.type == "memory" and n.id.startswith(prefix)
        ]
        if not matches:
            return "No current memory has that id."
        if len(matches) > 1:
            return "That id matches more than one memory. Give more characters."
        memory = matches[0]
        forget_memory(store, memory.id)
        return f"Forgot [{memory.id[:8]}] {memory.text}"
    finally:
        store.conn.close()


def main():
    # Load both models now, so the first tool call is fast and nothing prints later.
    with _quiet():
        embed_mod.get_model()
        get_extractor()
    mcp.run()


if __name__ == "__main__":
    main()