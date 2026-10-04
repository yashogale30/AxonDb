import json
from pathlib import Path

HERE = Path(__file__).parent

PROJECTS = [
    dict(name="Kestrel", desc="a ticket booking platform for concert venues",
         lang="Rust", db="PostgreSQL", cloud="AWS", tool="Redis",
         purpose="seat locking", cat="cache",
         lead="Aarav", lead_city="Pune", eng="Kavya", eng_city="Hyderabad"),
    dict(name="Marlin", desc="a fraud detection service for online banks",
         lang="Kotlin", db="MongoDB", cloud="Azure", tool="Kafka",
         purpose="streaming events", cat="event streaming platform",
         lead="Bianca", lead_city="Lisbon", eng="Liam", eng_city="Dublin"),
    dict(name="Quartz", desc="a mobile app for tracking daily habits",
         lang="Swift", db="DynamoDB", cloud="Google Cloud", tool="RabbitMQ",
         purpose="message queues", cat="message broker",
         lead="Chen", lead_city="Singapore", eng="Mei", eng_city="Shanghai"),
    dict(name="Falcon", desc="a search portal for legal documents",
         lang="Python", db="Cassandra", cloud="DigitalOcean", tool="Elasticsearch",
         purpose="document search", cat="search engine",
         lead="Dmitri", lead_city="Warsaw", eng="Nikhil", eng_city="Jaipur"),
    dict(name="Juniper", desc="an analytics dashboard for sales teams",
         lang="Elixir", db="ClickHouse", cloud="Oracle Cloud", tool="Grafana",
         purpose="dashboards", cat="dashboard tool",
         lead="Elena", lead_city="Madrid", eng="Olga", eng_city="Prague"),
    dict(name="Cobalt", desc="a data platform for energy companies",
         lang="TypeScript", db="CockroachDB", cloud="IBM Cloud", tool="Airflow",
         purpose="scheduling pipelines", cat="workflow scheduler",
         lead="Farid", lead_city="Dubai", eng="Pedro", eng_city="Bogota"),
    dict(name="Ember", desc="a notification service for email and SMS",
         lang="Scala", db="MariaDB", cloud="Hetzner", tool="Twilio",
         purpose="sending text messages", cat="SMS provider",
         lead="Gauri", lead_city="Bengaluru", eng="Qadir", eng_city="Karachi"),
    dict(name="Saffron", desc="an online shop for spices and tea",
         lang="Ruby", db="Firestore", cloud="Heroku", tool="Stripe",
         purpose="taking payments", cat="payment provider",
         lead="Hugo", lead_city="Toronto", eng="Rosa", eng_city="Lima"),
    dict(name="Tundra", desc="a sensor platform for cold storage warehouses",
         lang="Dart", db="TimescaleDB", cloud="Linode", tool="Prometheus",
         purpose="monitoring sensors", cat="monitoring tool",
         lead="Imani", lead_city="Nairobi", eng="Soren", eng_city="Copenhagen"),
    dict(name="Willow", desc="a learning app for school students",
         lang="Haskell", db="Couchbase", cloud="Vultr", tool="Memcached",
         purpose="caching lessons", cat="caching tool",
         lead="Jonas", lead_city="Oslo", eng="Talia", eng_city="Sydney"),
]

BY_NAME = {p["name"]: p for p in PROJECTS}
BY_LEAD = {p["lead"]: p for p in PROJECTS}
BY_ENG = {p["eng"]: p for p in PROJECTS}


def memories_for(p):
    return [
        f"{p['lead']} leads the {p['name']} project.",
        f"{p['name']} is {p['desc']}.",
        f"{p['name']} is built with {p['lang']}.",
        f"{p['name']} stores its data in {p['db']}.",
        f"{p['name']} is deployed on {p['cloud']}.",
        f"{p['name']} uses {p['tool']} for {p['purpose']}.",
        f"{p['eng']} is a backend engineer on the {p['name']} project.",
        f"{p['eng']} reports to {p['lead']}.",
        f"{p['eng']} lives in {p['eng_city']}.",
        f"{p['lead']} lives in {p['lead_city']}.",
    ]


def attr_question(ref, p, key):
    if key == "lang":
        return f"Which programming language is {ref} built with?"
    if key == "db":
        return f"Which database does {ref} use?"
    if key == "cloud":
        return f"Which cloud is {ref} deployed on?"
    return f"Which {p['cat']} does {ref} use?"


questions = []


def add(question, answer, hops):
    questions.append({"question": question, "answer": answer, "hops": hops})


# One hop: a project attribute asked directly, and an engineer's city.
ONE_HOP = {
    "Kestrel": ["db", "cloud"], "Marlin": ["lang", "tool"],
    "Quartz": ["db", "cloud"], "Falcon": ["lang", "tool"],
    "Juniper": ["db", "cloud"], "Cobalt": ["lang", "tool"],
    "Ember": ["db", "cloud"], "Saffron": ["lang", "tool"],
    "Tundra": ["db", "cloud"], "Willow": ["lang", "tool"],
}
for name, keys in ONE_HOP.items():
    p = BY_NAME[name]
    for key in keys:
        add(attr_question(name, p, key), p[key], 1)
for eng in ["Kavya", "Mei", "Olga", "Qadir", "Soren"]:
    add(f"Where does {eng} live?", BY_ENG[eng]["eng_city"], 1)

# Two hop: through the lead of a project.
TWO_HOP_LEAD = {
    "Aarav": ["lang", "tool", "cloud"], "Bianca": ["db", "cloud", "lang"],
    "Chen": ["lang", "tool", "db"], "Dmitri": ["db", "cloud", "lang"],
    "Elena": ["lang", "tool", "cloud"], "Farid": ["db", "cloud"],
    "Gauri": ["lang", "tool"], "Hugo": ["db", "cloud"],
    "Imani": ["lang", "tool"], "Jonas": ["db", "cloud"],
}
for lead, keys in TWO_HOP_LEAD.items():
    p = BY_LEAD[lead]
    ref = f"the project {lead} leads"
    for key in keys:
        add(attr_question(ref, p, key), p[key], 2)

# Two hop: the manager of an engineer, and two role style questions.
for p in PROJECTS:
    add(f"Where does the manager of {p['eng']} live?", p["lead_city"], 2)
for name in ["Marlin", "Falcon", "Cobalt", "Saffron", "Willow"]:
    add(f"Where does the person who leads {name} live?",
        BY_NAME[name]["lead_city"], 2)
for name in ["Kestrel", "Quartz", "Juniper", "Ember", "Tundra"]:
    add(f"Where does the backend engineer on {name} live?",
        BY_NAME[name]["eng_city"], 2)

# Three hop: engineer, then manager, then project, then an attribute.
THREE_HOP = {
    "Kavya": ["db", "cloud", "tool"], "Liam": ["lang", "cloud", "tool"],
    "Mei": ["lang", "db", "tool"], "Nikhil": ["lang", "db", "cloud"],
    "Olga": ["db", "cloud", "tool"], "Pedro": ["lang", "cloud", "tool"],
    "Qadir": ["lang", "db", "tool"], "Rosa": ["lang", "db", "cloud"],
    "Soren": ["db", "cloud", "tool"], "Talia": ["lang", "cloud", "tool"],
}
for eng, keys in THREE_HOP.items():
    p = BY_ENG[eng]
    ref = f"the project that {eng}'s manager leads"
    for key in keys:
        add(attr_question(ref, p, key), p[key], 3)

memories = []
for p in PROJECTS:
    memories.extend(memories_for(p))

# Safety checks: sizes, and every answer appears in exactly one memory.
assert len(memories) == 100, len(memories)
assert len(questions) == 100, len(questions)
texts = [m.lower() for m in memories]
for q in questions:
    count = sum(1 for t in texts if q["answer"].lower() in t)
    assert count == 1, (q["question"], q["answer"], count)

(HERE / "big_memories.json").write_text(json.dumps(memories, indent=2))
(HERE / "big_questions.json").write_text(json.dumps(questions, indent=2))

by_hops = {}
for q in questions:
    by_hops[q["hops"]] = by_hops.get(q["hops"], 0) + 1
print("memories", len(memories), "questions", len(questions), "by hops", by_hops)
print("every answer appears in exactly one memory: ok")