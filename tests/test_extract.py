from AxonDb.extract import extract


def test_simple_relation_is_clean():
    out = extract("Atlas uses Redis for seat locking.")
    assert out["relations"] == [("Atlas", "uses", "Redis")]


def test_project_suffix_is_snapped():
    out = extract("Priya leads the Atlas project.")
    assert ("Priya", "leads", "Atlas") in out["relations"]
    names = [n for n, _ in out["entities"]]
    assert "Atlas project" not in names


def test_multi_word_names_survive_and_common_phrases_do_not():
    out = extract("Orion is deployed on Google Cloud.")
    names = [n for n, _ in out["entities"]]
    assert "Google Cloud" in names
    assert out["relations"] == [("Orion", "deployed_on", "Google Cloud")]