"""
llm.py - LLM (Large Language Model) Integration Module

Uses Google Gemini API (new google-genai SDK) to convert a natural
language query into a valid SQL query based on the provided schema.
"""

import re
from google import genai

# -------------------------------------------------------
# CONFIGURATION — Your Gemini API key
# -------------------------------------------------------
GEMINI_API_KEY = "AIzaSyCsEc9Ad8dMmCSVN129UfE9GNT6ysk1A90"

# Use gemini-2.5-flash based on available models
GEMINI_MODEL = "gemini-2.5-flash"

# Create client using new google-genai SDK
client = genai.Client(api_key=GEMINI_API_KEY)


def build_prompt(schema: str, user_query: str) -> str:
    """
    Constructs the prompt sent to Gemini.

    Includes:
    - Full database schema (from RAG)
    - User's natural language question
    - Clear instructions to return ONLY the SQL query

    Args:
        schema (str): The database schema context.
        user_query (str): The user's natural language query.

    Returns:
        str: The complete prompt string.
    """
    prompt = f"""You are an expert SQL query generator.

Given the following SQLite database schema:

{schema}

Convert the following natural language question into a valid SQL query.

Rules:
1. Return ONLY the SQL query — no explanations, no markdown, no code blocks.
2. The query must be valid SQLite syntax.
3. Use only the tables and columns defined in the schema above.
4. Do NOT include ```sql or ``` — just the raw SQL text.
5. End the query with a semicolon.

Natural Language Question: {user_query}

SQL Query:"""
    return prompt


def generate_sql(schema: str, user_query: str) -> str:
    """
    Calls the Gemini API and returns a clean SQL query string.

    Args:
        schema (str): The database schema context (from RAG).
        user_query (str): The user's natural language question.

    Returns:
        str: The generated SQL query (cleaned, no markdown).

    Raises:
        Exception: If the Gemini API call fails.
    """
    prompt = build_prompt(schema, user_query)
    print(f"[LLM] Sending prompt to Gemini model: {GEMINI_MODEL}")

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        raw_output = response.text
        print(f"[LLM] Raw Gemini response:\n{raw_output}")

        # Clean up the response to extract pure SQL
        sql_query = clean_sql_output(raw_output)
        print(f"[LLM] Cleaned SQL query: {sql_query}")
        return sql_query

    except Exception as e:
        print(f"[LLM] Error calling Gemini API: {e}")
        raise Exception(f"Gemini API error: {str(e)}")


def clean_sql_output(raw_text: str) -> str:
    """
    Cleans the raw LLM output to extract only the SQL query.

    Handles:
    - ```sql ... ``` markdown blocks
    - ``` ... ``` generic code blocks
    - Leading/trailing whitespace
    - Extra explanation text before the SQL

    Args:
        raw_text (str): The raw text returned by the LLM.

    Returns:
        str: The extracted and cleaned SQL query string.
    """
    # Remove markdown code fences
    cleaned = re.sub(r"```(?:sql)?\s*", "", raw_text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()

    # Capture lines starting from the first SQL keyword
    lines = cleaned.splitlines()
    sql_lines = []
    in_sql = False

    for line in lines:
        stripped = line.strip()
        if not in_sql and re.match(
            r"^(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|PRAGMA)",
            stripped,
            re.IGNORECASE,
        ):
            in_sql = True

        if in_sql:
            sql_lines.append(line)

    if sql_lines:
        cleaned = "\n".join(sql_lines).strip()

    return cleaned
