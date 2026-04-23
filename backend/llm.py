"""
llm.py - LLM (Large Language Model) Integration Module

Uses Google Gemini API to convert a natural language query
into a valid SQL query based on the provided database schema.
"""

import re
import google.generativeai as genai

# -------------------------------------------------------
# CONFIGURATION — Replace with your actual Gemini API key
# -------------------------------------------------------
GEMINI_API_KEY = "AIzaSyCDpwqbJEHgTKnvbPczEy1aGJCpF1Thy-0"

# Gemini model to use (gemini-1.5-flash is fast and free-tier friendly)
GEMINI_MODEL = "gemini-2.5-flash"

# Configure the Gemini client once at module load
genai.configure(api_key=GEMINI_API_KEY)


def build_prompt(schema: str, user_query: str) -> str:
    """
    Constructs the prompt that will be sent to Gemini.

    The prompt includes:
    - The full database schema (from RAG)
    - The user's natural language question
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
    Calls the Gemini API with the constructed prompt and
    returns a clean SQL query string.

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
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
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

    Handles common LLM response formats:
    - ```sql ... ``` markdown blocks
    - ``` ... ``` generic code blocks
    - Leading/trailing whitespace
    - Extra explanation text

    Args:
        raw_text (str): The raw text returned by the LLM.

    Returns:
        str: The extracted and cleaned SQL query string.
    """
    # Remove markdown code fences (```sql ... ``` or ``` ... ```)
    cleaned = re.sub(r"```(?:sql)?\s*", "", raw_text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")

    # Strip leading/trailing whitespace and newlines
    cleaned = cleaned.strip()

    # If multiple lines, take lines that look like SQL
    # (starts with SELECT, WITH, INSERT, UPDATE, DELETE, etc.)
    lines = cleaned.splitlines()
    sql_lines = []
    in_sql = False

    for line in lines:
        stripped = line.strip()
        # Start capturing at the first SQL keyword
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
