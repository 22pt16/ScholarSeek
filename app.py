import uuid
print("Loading ScholarSeek Search Engine...")
from flask import Flask, render_template, request, jsonify
from search_engine import SearchEngine

app = Flask(__name__)
engine = SearchEngine(load_sample_corpus=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()
    algo = request.args.get("algo", "tfidf").strip().lower()
    expand = request.args.get("expand", "false").lower() == "true"

    if not query:
        return jsonify({
            "query": "",
            "results": [],
            "total_results": 0,
            "execution_time_ms": 0,
            "suggestion": None,
            "algorithm": algo.upper(),
            "expanded_terms": [],
        })

    result = engine.search(query, algorithm=algo, expand_query=expand)
    return jsonify(result)

@app.route("/api/suggest", methods=["GET"])
def api_suggest():
    query = request.args.get("q", "").strip()
    suggestions = engine.autocomplete(query)
    return jsonify({"prefix": query, "suggestions": suggestions})

@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(engine.get_stats())

@app.route("/api/expand", methods=["GET"])
def api_expand():
    """Preview query expansion terms without executing a full search."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"query": query, "expansions": []})
    expansions = engine.get_expand_preview(query, top_n=8)
    return jsonify({"query": query, "expansions": expansions})

@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    """
    Evaluate multiple ranking algorithms against user-provided ground truth.

    Request body (JSON):
    {
        "query": "deep learning",
        "relevant_ids": ["1901.00123", "1802.04567", ...],
        "algorithms": ["tfidf", "bm25", "field_aware", "semantic", "hybrid"],
        "k": 10
    }
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    relevant_ids = data.get("relevant_ids", [])
    algorithms = data.get("algorithms", None)
    k = int(data.get("k", 10))

    if not query or not relevant_ids:
        return jsonify({"error": "query and relevant_ids are required"}), 400

    result = engine.evaluate_query(
        query=query,
        relevant_ids=relevant_ids,
        algorithms=algorithms,
        top_k=k,
    )
    return jsonify(result)

@app.route("/api/documents", methods=["POST"])
def api_add_document():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category = data.get("category", "General").strip()
    url = data.get("url", "#").strip()

    if not title or not content:
        return jsonify({"error": "Title and content are required."}), 400

    doc_id = f"doc_{uuid.uuid4().hex[:6]}"
    engine.index_document(doc_id, title, content, category, url)

    return jsonify({
        "message": "Document indexed successfully!",
        "doc_id": doc_id,
        "stats": engine.get_stats()
    }), 201

if __name__ == "__main__":
    print("Starting ScholarSeek on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000, use_reloader=False)
