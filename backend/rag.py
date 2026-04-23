"""
rag.py - RAG (Retrieval-Augmented Generation) Module

Implements a Hybrid NLP Pipeline combining classic Natural Language Processing
(Tokenization, POS tagging, Lemmatization, TF-IDF) with Cosine Similarity
to retrieve only the most mathematically relevant tables from the schema.
"""

import os
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Path to the schema file
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.txt")

# Initialize global NLP components
lemmatizer = WordNetLemmatizer()
vectorizer = TfidfVectorizer(stop_words='english')
table_schemas = []
table_vectors = None

def get_wordnet_pos(treebank_tag):
    """Maps POS tag to first character for lemmatizer"""
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

def preprocess_text(text: str) -> str:
    """
    Classic NLP Pipeline Step:
    1. Tokenize into words
    2. Tag parts of speech (POS)
    3. Lemmatize back to root word form
    """
    tokens = nltk.word_tokenize(text.lower())
    pos_tags = nltk.pos_tag(tokens)
    lemmas = []
    for word, tag in pos_tags:
        if word.isalnum():
            w_pos = get_wordnet_pos(tag)
            lemmas.append(lemmatizer.lemmatize(word, w_pos))
    return " ".join(lemmas)

def init_rag():
    """Reads the schema, splits by table, and builds the TF-IDF vector index."""
    global table_schemas, table_vectors
    if not os.path.exists(SCHEMA_FILE):
        return

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by CREATE TABLE
    raw_tables = content.split("CREATE TABLE")
    table_schemas = []
    for chunk in raw_tables:
        chunk = chunk.strip()
        if not chunk or chunk.startswith("--"):
            continue
        
        full_table_sql = "CREATE TABLE " + chunk
        table_schemas.append(full_table_sql)
        
    print(f"\n[RAG] Booting Classic NLP Pipeline...")
    print(f"[RAG] Parsed {len(table_schemas)} database tables from schema.")
    
    # Preprocess each table schema for TF-IDF indexing
    print("[RAG] Running semantic indexing (Tokenization -> POS Tagging -> Lemmatization)...")
    processed_schemas = [preprocess_text(schema) for schema in table_schemas]
    table_vectors = vectorizer.fit_transform(processed_schemas)
    print("[RAG] TF-IDF Vectorizer successfully fitted on schema vocabulary.\n")

def get_relevant_schema(user_query: str, top_n=3) -> str:
    """
    Smart Retrieval Step:
    Uses Cosine Similarity between the TF-IDF vectors of the query
    and the tables to retrieve only the top matching tables.
    """
    if not table_schemas or table_vectors is None:
        init_rag()
        
    if not table_schemas:
        return ""

    print(f"[RAG] Processing query via NLP pipeline: '{user_query}'")
    processed_query = preprocess_text(user_query)
    print(f"[RAG] Lemmatized Query string: '{processed_query}'")
    
    query_vector = vectorizer.transform([processed_query])
    similarities = cosine_similarity(query_vector, table_vectors).flatten()
    
    # Get indices of top_n most similar tables
    top_indices = similarities.argsort()[-top_n:][::-1]
    
    relevant_schemas = []
    scores = []
    for idx in top_indices:
        relevant_schemas.append(table_schemas[idx])
        scores.append(round(similarities[idx], 3))

    final_context = "\n\n".join(relevant_schemas)
    print(f"[RAG] Isolated Top {top_n} Tables. Cosine Similarity Scores: {scores}")
    return final_context
