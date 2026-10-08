import uuid
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
    
    if not query:
        return jsonify({
            "query": "",
            "results": [],
            "total_results": 0,
            "execution_time_ms": 0,
            "suggestion": None,
            "algorithm": algo.upper()
        })

    result = engine.search(query, algorithm=algo)
    return jsonify(result)

@app.route("/api/suggest", methods=["GET"])
def api_suggest():
    query = request.args.get("q", "").strip()
    suggestions = engine.autocomplete(query)
    return jsonify({"prefix": query, "suggestions": suggestions})

@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(engine.get_stats())

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
    print("🚀 Starting Mini Search Engine Web Server on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
