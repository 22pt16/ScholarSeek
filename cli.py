import sys
from search_engine import SearchEngine

def main():
    print("=" * 60)
    print("  🔍 MINI SEARCH ENGINE CLI - Information Retrieval System")
    print("=" * 60)
    
    engine = SearchEngine(load_sample_corpus=True)
    stats = engine.get_stats()
    print(f"📊 Corpus Loaded: {stats['total_documents']} Documents | Vocabulary: {stats['vocabulary_size']} Terms")
    print("Commands:")
    print("  :tfidf | :bm25 | :field_aware | :semantic | :hybrid  - Switch algorithm")
    print("  :expand on | :expand off                             - Toggle query expansion")
    print("  :eval                                                - Benchmark algorithms")
    print("  :exit                                                - Quit\n")

    current_algo = "tfidf"
    expand_enabled = False
    last_query = ""

    while True:
        try:
            status_tag = f"{current_algo.upper()}{'+EXPAND' if expand_enabled else ''}"
            query = input(f"\n[Search ({status_tag})]> ").strip()
            
            if not query:
                continue

            if query == ":exit":
                print("Goodbye!")
                break
            elif query in (":tfidf", ":bm25", ":field_aware", ":semantic", ":hybrid"):
                current_algo = query[1:]
                print(f"Switched algorithm to {current_algo.upper()}")
                continue
            elif query == ":expand on":
                expand_enabled = True
                print("Query expansion ENABLED.")
                continue
            elif query == ":expand off":
                expand_enabled = False
                print("Query expansion DISABLED.")
                continue
            elif query.startswith(":eval"):
                # Evaluation runner
                eq = input("Enter query to evaluate (leave empty to use last query): ").strip() or last_query
                if not eq:
                    print("No query specified.")
                    continue
                rel_raw = input("Enter comma-separated relevant document IDs (arXiv IDs): ").strip()
                rel_ids = [r.strip() for r in rel_raw.split(",") if r.strip()]
                if not rel_ids:
                    print("No relevant IDs provided.")
                    continue
                
                print(f"\nRunning evaluation on '{eq}' against {len(rel_ids)} relevant docs...")
                eval_res = engine.evaluate_query(eq, rel_ids, top_k=10)
                
                header = f"{'Algorithm':<14} | {'P@10':<7} | {'R@10':<7} | {'F1@10':<7} | {'NDCG@10':<8} | {'MRR':<7} | {'Time(ms)':<8}"
                print("-" * len(header))
                print(header)
                print("-" * len(header))
                for algo, m in eval_res["metrics"].items():
                    if "error" in m:
                        print(f"{algo:<14} | Error: {m['error']}")
                    else:
                        print(f"{algo:<14} | {m.get('precision@10', 0):.4f}  | {m.get('recall@10', 0):.4f}  | {m.get('f1@10', 0):.4f}  | {m.get('ndcg@10', 0):.4f}   | {m.get('mrr', 0):.4f}  | {m.get('execution_time_ms', 0):.1f}")
                print("-" * len(header))
                continue

            last_query = query
            response = engine.search(query, algorithm=current_algo, expand_query=expand_enabled)

            print("-" * 60)
            if response.get("expanded_terms"):
                print(f"🔍 Expanded Terms: {', '.join(response['expanded_terms'])}")
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
