from search_engine import SearchEngine


def build_engine():
    engine = SearchEngine(load_sample_corpus=False)
    engine.index_document(
        "paper-1", "Machine learning methods", "machine learning models improve classification",
        category="cs.LG", url="https://arxiv.org/abs/paper-1"
    )
    engine.index_document(
        "paper-2", "Database indexing", "indexing improves database query retrieval",
        category="cs.DB", url="https://arxiv.org/abs/paper-2"
    )
    engine.index_document(
        "paper-3", "Learning for graphs", "graph learning and machine learning approaches",
        category="cs.LG", url="https://arxiv.org/abs/paper-3"
    )
    return engine


def test_tfidf_and_bm25_return_matching_results():
    engine = build_engine()
    for algorithm in ("tfidf", "bm25"):
        result = engine.search("machine learning", algorithm=algorithm, top_k=2)
        assert result["results"]
        assert result["results"][0]["id"] in {"paper-1", "paper-3"}
        assert result["algorithm"] == algorithm.upper()


def test_total_results_is_match_count_not_page_size():
    engine = build_engine()
    result = engine.search("learning", algorithm="bm25", top_k=1)
    assert len(result["results"]) == 1
    assert result["total_results"] == 2


def test_autocomplete_returns_prefix_matches():
    engine = build_engine()
    matches = engine.autocomplete("learn", limit=5)
    assert matches
    assert all(term.startswith("learn") for term in matches)


def test_bounded_levenshtein_distance():
    from search_engine.spell_check import SpellChecker
    assert SpellChecker.levenshtein_distance("machien", "machine", 2) == 2
    assert SpellChecker.levenshtein_distance("kitten", "sitting", 2) == 3


def test_spell_suggestion_uses_surface_words():
    engine = build_engine()
    suggestion, changed = engine.spell_checker.suggest_query(
        "machien learning",
        tokenizer=engine.tokenizer,
        indexed_vocabulary=engine.index.vocabulary,
    )
    assert changed
    assert suggestion.startswith("machine ")


def test_semantic_search_returns_ranked_results():
    engine = build_engine()
    result = engine.search("machine learning", algorithm="semantic", top_k=2)
    assert result["algorithm"] == "SEMANTIC"
    assert len(result["results"]) == 2
    assert result["results"][0]["id"] in {"paper-1", "paper-3"}
    assert "semantic" in result["results"][0]["term_scores"]
    assert result["results"][0]["score"] > 0


def test_semantic_search_incremental_indexing():
    engine = build_engine()
    # Initialize semantic search
    res1 = engine.search("quantum cryptography", algorithm="semantic", top_k=1)
    
    # Now dynamically add a quantum paper
    engine.index_document(
        "paper-q1",
        "Quantum Cryptography and Security",
        "Protocols for quantum key distribution and secure quantum communication",
        category="quant-ph",
        url="https://arxiv.org/abs/paper-q1"
    )
    res2 = engine.search("quantum key distribution", algorithm="semantic", top_k=1)
    assert len(res2["results"]) > 0
    assert res2["results"][0]["id"] == "paper-q1"
