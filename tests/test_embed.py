import numpy as np

from AxonDb.embed import embed, embed_many, similarities


def test_vector_shape_and_length():
    v = embed("Priya leads the Atlas project")
    assert v.shape == (384,)
    assert np.isclose(np.linalg.norm(v), 1.0, atol=1e-3)


def test_similar_sentences_score_higher():
    a = embed("Priya leads the Atlas project")
    b = embed("Atlas is led by Priya")
    c = embed("I love eating mangoes in summer")
    assert float(a @ b) > float(a @ c)


def test_similarities_against_matrix():
    matrix = embed_many([
        "Priya leads the Atlas project",
        "I love eating mangoes in summer",
    ])
    query = embed("Who is in charge of Atlas?")
    scores = similarities(query, matrix)
    assert scores.shape == (2,)
    assert scores[0] > scores[1]