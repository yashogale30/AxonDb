from AxonDb.models import Edge, Node
from AxonDb.store import SqliteStore, new_id, vec_to_bytes


def make_store(tmp_path):
    return SqliteStore(tmp_path / "test.db")


def entity(name, kind="person", embedding=None):
    return Node(id=new_id(), type=kind, name=name, embedding=embedding)


def test_add_and_get_node(tmp_path):
    store = make_store(tmp_path)
    node = store.add_node(entity("Priya"))
    found = store.get_node(node.id)
    assert found.name == "Priya"
    assert found.valid_to is None


def test_find_entity_ignores_case_and_spaces(tmp_path):
    store = make_store(tmp_path)
    store.add_node(entity("Priya"))
    assert store.find_entity("  priya ") is not None
    assert store.find_entity("Atlas") is None


def test_memory_nodes_are_not_entities(tmp_path):
    store = make_store(tmp_path)
    store.add_node(Node(id=new_id(), type="memory", name="Priya", text="Priya leads Atlas"))
    assert store.find_entity("Priya") is None


def test_neighbors_both_directions_and_close_edge(tmp_path):
    store = make_store(tmp_path)
    a = store.add_node(entity("Priya"))
    b = store.add_node(entity("Atlas", "project"))
    edge = store.add_edge(Edge(id=new_id(), src=a.id, dst=b.id, rel="leads"))
    assert len(store.neighbors(a.id)) == 1
    assert len(store.neighbors(b.id)) == 1
    store.close_edge(edge.id)
    assert len(store.neighbors(a.id)) == 0


def test_all_embeddings_and_type_filter(tmp_path):
    store = make_store(tmp_path)
    store.add_node(entity("Priya", embedding=vec_to_bytes([1, 0, 0])))
    store.add_node(Node(id=new_id(), type="memory", name="m1", embedding=vec_to_bytes([0, 1, 0])))
    ids, matrix = store.all_embeddings()
    assert matrix.shape == (2, 3)
    ids, matrix = store.all_embeddings(types=["memory"])
    assert matrix.shape == (1, 3)


def test_close_node_hides_node_and_edges(tmp_path):
    store = make_store(tmp_path)
    a = store.add_node(entity("Priya"))
    b = store.add_node(entity("Atlas", "project"))
    store.add_edge(Edge(id=new_id(), src=a.id, dst=b.id, rel="leads"))
    store.close_node(a.id)
    assert store.find_entity("Priya") is None
    assert store.neighbors(b.id) == []
    assert len(store.all_nodes()) == 1