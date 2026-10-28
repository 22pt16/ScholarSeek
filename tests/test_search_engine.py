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
