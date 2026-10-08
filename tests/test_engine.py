import unittest
from search_engine.tokenizer import Tokenizer, simple_stem
from search_engine.inverted_index import InvertedIndex
from search_engine.ranker import Ranker
from search_engine.spell_check import SpellChecker
from search_engine.engine import SearchEngine

class TestMiniSearchEngine(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer()
        self.index = InvertedIndex()

    def test_tokenizer_basic(self):
        text = "Data structures and algorithms in Python!!"
        tokens = self.tokenizer.tokenize(text)
        self.assertIn("data", tokens)
        self.assertIn("structur", tokens)  # Stemmed form
        self.assertIn("algorithm", tokens) # Stemmed form
        self.assertNotIn("and", tokens)    # Stop word removed
        self.assertNotIn("in", tokens)     # Stop word removed

    def test_inverted_index(self):
        tokens_1 = [("data", 0, 0, 4), ("algorithm", 1, 5, 14)]
        tokens_2 = [("data", 0, 0, 4), ("python", 1, 5, 11)]

        self.index.add_document("doc1", "Doc One", "data algorithm", tokens_with_pos=tokens_1)
        self.index.add_document("doc2", "Doc Two", "data python", tokens_with_pos=tokens_2)

        self.assertEqual(self.index.total_documents, 2)
        self.assertEqual(self.index.get_document_frequency("data"), 2)
        self.assertEqual(self.index.get_document_frequency("algorithm"), 1)

    def test_ranking_tfidf(self):
        engine = SearchEngine(load_sample_corpus=False)
        engine.index_document("d1", "AI and Machine Learning", "Artificial intelligence uses statistical learning algorithms.")
        engine.index_document("d2", "Web Frameworks", "Flask is a web framework written in Python.")

        res = engine.search("machine learning", algorithm="tfidf")
        self.assertTrue(len(res["results"]) > 0)
        self.assertEqual(res["results"][0]["id"], "d1")

    def test_ranking_bm25(self):
        engine = SearchEngine(load_sample_corpus=False)
        engine.index_document("d1", "AI and Machine Learning", "Artificial intelligence uses statistical learning algorithms.")
        engine.index_document("d2", "Web Frameworks", "Flask is a web framework written in Python.")

        res = engine.search("machine learning", algorithm="bm25")
        self.assertTrue(len(res["results"]) > 0)
        self.assertEqual(res["results"][0]["id"], "d1")

    def test_spell_checker_levenshtein(self):
        vocab = {"algorithm", "structure", "database", "python"}
        speller = SpellChecker(vocab)

        # Test distance
        dist = SpellChecker.levenshtein_distance("algoritm", "algorithm")
        self.assertEqual(dist, 1)

        # Test suggestion
        suggested = speller.suggest("algoritm")
        self.assertEqual(suggested, "algorithm")

    def test_autocomplete(self):
        engine = SearchEngine(load_sample_corpus=True)
        suggestions = engine.autocomplete("data")
        self.assertTrue(len(suggestions) > 0)

if __name__ == "__main__":
    unittest.main()
