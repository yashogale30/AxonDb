import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

here = Path(__file__).parent
memories = json.loads((here / "demo_memories.json").read_text())
questions = json.loads((here / "demo_questions.json").read_text())
questions = [q["question"] if isinstance(q, dict) else q for q in questions]

# The memory that answers each question, in the same order as demo_questions.json.
ANSWERS = [
    "Atlas uses Redis for seat locking.",
    "Atlas is deployed on AWS.",
    "Orion uses Kafka for streaming events.",
    "Atlas stores its bookings in Postgres.",
    "Meera prefers working in Figma.",
    "Priya moved from Pune to Mumbai last month.",
]

# (model name, text added in front of every question)
MODELS = [
    ("all-MiniLM-L6-v2", ""),
    ("multi-qa-MiniLM-L6-cos-v1", ""),
    ("BAAI/bge-small-en-v1.5",
     "Represent this sentence for searching relevant passages: "),
]


def find(text):
    for i, m in enumerate(memories):
        if m.strip() == text:
            return i
    raise SystemExit(f"Answer not found in demo_memories.json: {text}")


answer_ids = [find(a) for a in ANSWERS]
results = {}

for name, prefix in MODELS:
    print("loading", name)
    model = SentenceTransformer(name)
    matrix = model.encode(memories, normalize_embeddings=True)
    row = []
    for question, answer_id in zip(questions, answer_ids):
        q = model.encode(prefix + question, normalize_embeddings=True)
        sims = matrix @ q
        order = list(sims.argsort()[::-1])
        row.append((order.index(answer_id) + 1, float(sims[answer_id])))
    results[name] = row

print()
print("Rank of the answer memory among 20 (1 is best), with its score")
for n, question in enumerate(questions):
    print()
    print(f"Q{n + 1}: {question[:60]}")
    for name, _prefix in MODELS:
        rank, score = results[name][n]
        print(f"    {name:28} rank {rank:2}  score {score:.2f}")