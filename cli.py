import sys
from search_engine import SearchEngine

def main():
    print("=" * 60)
    print("  🔍 MINI SEARCH ENGINE CLI - Information Retrieval System")
    print("=" * 60)
    
    engine = SearchEngine(load_sample_corpus=True)
    stats = engine.get_stats()
    print(f"📊 Corpus Loaded: {stats['total_documents']} Documents | Vocabulary: {stats['vocabulary_size']} Terms")
    print("Commands: type your query to search, ':bm25' or ':tfidf' to switch ranking algorithm, or ':exit' to quit.\n")

    current_algo = "tfidf"

    while True:
        try:
            query = input(f"\n[Search ({current_algo.upper()})]> ").strip()
            
            if not query:
                continue

            if query == ":exit":
                print("Goodbye!")
                break
            elif query in (":tfidf", ":bm25"):
                current_algo = query[1:]
                print(f"Switched algorithm to {current_algo.upper()}")
                continue

            response = engine.search(query, algorithm=current_algo)

            print("-" * 60)
            if response["suggestion"]:
                print(f"💡 Did you mean: '{response['suggestion']}'?")

            print(f"Found {response['total_results']} results in {response['execution_time_ms']} ms ({response['algorithm']}):\n")

            if not response["results"]:
                print("  No documents matched your query.")
            else:
                for idx, item in enumerate(response["results"], 1):
                    print(f" [{idx}] {item['title']}  (Score: {item['score']}) [{item['category']}]")
                    print(f"     URL: {item['url']}")
                    print(f"     Snippet: {item['snippet']}")
                    print(f"     Terms: {item['term_scores']}")
                    print()
            print("-" * 60)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting search CLI.")
            break

if __name__ == "__main__":
    main()
