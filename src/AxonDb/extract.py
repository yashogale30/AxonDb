import re

from .config import (ENTITY_THRESHOLD, GLINER_MODEL, LABELS, RELATION_CUES,
                     RELATIONS)

_extractor = None


def get_extractor():
    """Load the model once, the first time it is needed."""
    global _extractor
    if _extractor is None:
        from gliner2 import GLiNER2
        _extractor = GLiNER2.from_pretrained(GLINER_MODEL)
    return _extractor


def raw_extract(text):
    """Untouched model output. Useful for looking at what the model returns."""
    ex = get_extractor()
    try:
        ents = ex.extract_entities(text, LABELS, threshold=ENTITY_THRESHOLD)
    except TypeError:
        ents = ex.extract_entities(text, LABELS)
    rels = ex.extract_relations(text, RELATIONS)
    return ents, rels


def _text(value):
    if isinstance(value, dict):
        value = value.get("text") or value.get("name") or ""
    return " ".join(str(value).split()).strip(" .,;:")


def _pair(item):
    if isinstance(item, dict):
        head = item.get("head") or item.get("source") or item.get("subject")
        tail = item.get("tail") or item.get("target") or item.get("object")
        return head, tail
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[0], item[1]
    return None, None


def _is_entity(name):
    """Keep named things. Drop lowercase multi word phrases like 'concert venues'."""
    return len(name) > 1 and (name[0].isupper() or " " not in name)


def _has_cue(relation, sentence):
    """Only trust a relation if its trigger word really appears in the sentence."""
    low = sentence.lower()
    for stem in RELATION_CUES.get(relation, []):
        if re.search(r"\b" + re.escape(stem), low):
            return True
    return False


def _snap(name, known):
    """Map 'Atlas project' to the entity 'Atlas'. Return None if nothing matches."""
    low = name.lower()
    if low in known:
        return known[low]
    best = None
    for key, original in known.items():
        if key in low and (best is None or len(key) > len(best[0])):
            best = (key, original)
    return best[1] if best else None


def extract(text):
    """Return {'entities': [(name, label)], 'relations': [(head, rel, tail)]}."""
    ents_raw, rels_raw = raw_extract(text)

    entities = []
    known = {}
    for label, names in ents_raw.get("entities", ents_raw).items():
        for name in names:
            name = _text(name)
            if name and _is_entity(name) and name.lower() not in known:
                known[name.lower()] = name
                entities.append((name, label))

    relations = []
    for rel, items in rels_raw.get("relation_extraction", rels_raw).items():
        if not _has_cue(rel, text):
            continue
        for item in items:
            head, tail = _pair(item)
            head = _snap(_text(head or ""), known)
            tail = _snap(_text(tail or ""), known)
            if not head or not tail or head == tail:
                continue
            triple = (head, rel, tail)
            if triple not in relations:
                relations.append(triple)

    return {"entities": entities, "relations": relations}