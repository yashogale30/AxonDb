from AxonDb.embed import embed, similarities

PAIRS = [
    ("Atlas", "Atlas project"),
    ("Postgres", "PostgreSQL"),
    ("Priya", "Priya Sharma"),
    ("Mumbai", "Pune"),
    ("Redis", "Postgres"),
    ("Kafka", "Redis"),
]

for a, b in PAIRS:
    score = float(similarities(embed(a), embed(b)[None, :])[0])
    print(f"{a!r:14} vs {b!r:16} {score:.2f}")