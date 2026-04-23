"""
db.py - Database Module

Handles all SQLite (Chinook DB) connections and query execution.
- Connects to chinook.db located in the backend/ directory
- Executes SQL queries safely
- Returns results as a list of dictionaries (JSON-serializable)
"""

import sqlite3
import os

# Path to the Northwind SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "northwind.db")


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a new SQLite connection to chinook.db.

    The connection uses Row factory so columns are accessible
    by name (like a dict), not just by index.

    Returns:
        sqlite3.Connection: A live connection to the database.

    Raises:
        FileNotFoundError: If chinook.db does not exist.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database file not found at: {DB_PATH}\n"
            "Please download northwind.db and place it in the backend/ directory.\n"
            "Download link: https://github.com/jpwhite3/northwind-SQLite3"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables dict-like row access
    print(f"[DB] Connected to database: {DB_PATH}")
    return conn


def execute_query(sql: str) -> list[dict]:
    """
    Executes the given SQL query against the Chinook database
    and returns the results as a list of dictionaries.

    Args:
        sql (str): A valid SQLite SELECT query.

    Returns:
        list[dict]: A list of rows, each represented as a dictionary
                    mapping column names to values.

    Raises:
        ValueError: If the SQL query is empty or None.
        sqlite3.Error: If query execution fails (syntax error, etc.).
        Exception: For any other unexpected errors.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query is empty. Cannot execute.")

    print(f"[DB] Executing SQL:\n{sql}")

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Execute the query (read-only SELECT queries only for safety)
        cursor.execute(sql)

        # Fetch all results and convert to list of dicts
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        print(f"[DB] Query returned {len(results)} row(s)")
        return results

    except sqlite3.OperationalError as e:
        print(f"[DB] SQL OperationalError: {e}")
        raise sqlite3.OperationalError(f"SQL execution failed: {str(e)}")

    except sqlite3.Error as e:
        print(f"[DB] SQLite error: {e}")
        raise sqlite3.Error(f"Database error: {str(e)}")

    except Exception as e:
        print(f"[DB] Unexpected error: {e}")
        raise Exception(f"Unexpected database error: {str(e)}")

    finally:
        if conn:
            conn.close()
            print("[DB] Connection closed.")
