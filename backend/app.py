"""
app.py - Flask Application Entry Point

This is the main Flask server for the RAG-Based Text-to-SQL Query Generator.

Endpoints:
  POST /query  - Accepts a natural language query, generates SQL via Gemini,
                 executes it on the Chinook SQLite database, and returns results.

Run with:
  python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

from rag import get_relevant_schema, init_rag, preprocess_text
from llm import generate_sql
from db import execute_query

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes (required for frontend fetch calls)
CORS(app)


# -------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    """Simple health check to verify the server is running."""
    return jsonify({
        "status": "ok",
        "message": "RAG Text-to-SQL Query Generator is running!",
        "usage": "POST /query with JSON body: { \"query\": \"your question here\" }"
    })


# -------------------------------------------------------
# Main Query Endpoint
# -------------------------------------------------------
@app.route("/query", methods=["POST"])
def handle_query():
    """
    Accepts a natural language query and:
    1. Loads database schema via RAG
    2. Generates SQL using Gemini LLM
    3. Executes the SQL on Chinook DB
    4. Returns the SQL + results as JSON

    Request Body (JSON):
        {
            "query": "List all artists"
        }

    Response (JSON):
        {
            "success": true,
            "natural_language_query": "List all artists",
            "generated_sql": "SELECT Name FROM Artist;",
            "results": [{"Name": "AC/DC"}, ...]
        }
    """
    # --- Parse Request ---
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Request body must be JSON with a 'query' field."
        }), 400

    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({
            "success": False,
            "error": "The 'query' field cannot be empty."
        }), 400

    # --- Classic NLP Validation Layer ---
    # We clean the input and ensure there are actual semantic words (after removing stop words)
    cleaned_query = preprocess_text(user_query)
    if len(cleaned_query.strip()) == 0:
        return jsonify({
            "success": False,
            "error": "NLP Filter: Your request contained no meaningful nouns or verbs. Please ask a complete question."
        }), 400

    print(f"\n{'='*60}")
    print(f"[APP] Received query: {user_query}")
    print(f"{'='*60}")

    # --- Step 1: RAG — Load Schema Context ---
    try:
        schema = get_relevant_schema(user_query)
    except FileNotFoundError as e:
        print(f"[APP] Schema file error: {e}")
        return jsonify({
            "success": False,
            "error": f"Schema loading failed: {str(e)}"
        }), 500

    # --- Step 2: LLM — Generate SQL from Gemini ---
    try:
        generated_sql = generate_sql(schema, user_query)
    except Exception as e:
        print(f"[APP] LLM error: {e}")
        return jsonify({
            "success": False,
            "error": f"SQL generation failed: {str(e)}",
            "hint": "Check your Gemini API key in backend/llm.py"
        }), 500

    if not generated_sql:
        return jsonify({
            "success": False,
            "error": "The LLM returned an empty SQL query. Please rephrase your question.",
            "natural_language_query": user_query
        }), 422

    # --- Step 3: DB — Execute SQL on Chinook ---
    try:
        results = execute_query(generated_sql)
    except FileNotFoundError as e:
        print(f"[APP] Database file error: {e}")
        return jsonify({
            "success": False,
            "error": f"Database not found: {str(e)}",
            "generated_sql": generated_sql,
            "hint": "Download chinook.db to the backend/ directory."
        }), 500
    except sqlite3.OperationalError as e:
        print(f"[APP] SQL execution error: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid SQL query: {str(e)}",
            "generated_sql": generated_sql,
            "natural_language_query": user_query,
            "hint": "The generated SQL had a syntax error. Try rephrasing your question."
        }), 422
    except Exception as e:
        print(f"[APP] Unexpected DB error: {e}")
        return jsonify({
            "success": False,
            "error": f"Database execution error: {str(e)}",
            "generated_sql": generated_sql
        }), 500

    # --- Step 4: Return Success Response ---
    print(f"[APP] Success! Returning {len(results)} result(s).")
    return jsonify({
        "success": True,
        "natural_language_query": user_query,
        "generated_sql": generated_sql,
        "row_count": len(results),
        "results": results
    })


# -------------------------------------------------------
# Run the App
# -------------------------------------------------------
if __name__ == "__main__":
    init_rag()
    print("\n" + "="*60)
    print("  RAG-Based Text-to-SQL Query Generator")
    print("  Backend server starting on http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
