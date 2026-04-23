# RAG-Based Text-to-SQL Query Generator

This project is a powerful web application that transforms user-provided natural language queries into executable SQL commands. It leverages a Retrieval-Augmented Generation (RAG) architecture combined with traditional Natural Language Processing (NLP) and the Google Gemini Large Language Model (LLM) to accurately generate and execute SQL queries on a local SQLite database.

## Features

- **Natural Language to SQL**: Ask questions in plain English and automatically translate them to SQL.
- **Classic NLP Pipeline**: Utilizes tokenization, part-of-speech (POS) tagging, and lemmatization (via NLTK) to preprocess the database schema and user queries.
- **Smart RAG Retrieval**: Uses TF-IDF vectorization and Cosine Similarity to identify and retrieve only the most relevant database table schemas for the given query, reducing the context window and improving LLM accuracy.
- **LLM Integration**: Employs the Google Gemini API (specifically `gemini-2.5-flash`) to generate clean, valid SQLite queries based on the curated schema context and user input.
- **Immediate Execution**: Automatically executes the generated SQL query against a local SQLite database (e.g., Northwind or Chinook) and returns the formatted results.
- **Responsive GUI**: A frontend interface (HTML, CSS, JS) that offers an intuitive way to input questions and view the resulting SQL and data.

## Project Structure

```
NLP_CBP/
├── backend/
│   ├── app.py             # Main Flask application entry point and HTTP endpoints
│   ├── db.py              # SQLite database connection and query execution handler
│   ├── llm.py             # Google Gemini API integration and prompt engineering
│   ├── rag.py             # NLP pipeline (NLTK) and schema retrieval (TF-IDF, Cosine Similarity)
│   ├── schema.txt         # Text file containing the DDL (CREATE TABLE statements) for the database
│   ├── chinook.db         # Example SQLite database (optional)
│   └── northwind.db       # Primary SQLite database used by default
├── frontend/
│   ├── app.js             # Frontend logic to handle UI interactions and API calls
│   ├── index.html         # Main user interface
│   ├── server.py          # Optional simple HTTP server for frontend files
│   └── style.css          # Styling for the application
├── requirements.txt       # Python dependencies required to run the project
└── .vscode/               # VS Code workspace settings
```

## Prerequisites

- **Python 3.8+**
- **Google Gemini API Key**: You will need an API key from Google AI Studio to run the LLM component.

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Amreen-vnrvjiet/RAG-based-Text-to-SQL-Generation.git
   cd RAG-based-Text-to-SQL-Generation
   ```

2. **Set up a virtual environment (Recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **NLTK Data Download**: 
   The application requires specific NLTK datasets for the NLP pipeline. You may need to run this in python if NLTK throws errors:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('averaged_perceptron_tagger')
   nltk.download('wordnet')
   ```

5. **Configure API Key**:
   Open `backend/llm.py` and replace the placeholder `GEMINI_API_KEY` with your actual Google Gemini API key.
   > **Note:** For production use, it is highly recommended to use a `.env` file instead of hardcoding the API key.

6. **Database Setup**:
   Ensure `northwind.db` is located inside the `backend/` directory. The application uses this database to run queries against.

## Running the Application

The application consists of a backend Flask server and a static frontend.

1. **Start the Backend Server**:
   ```bash
   cd backend
   python app.py
   ```
   The Flask server will start running on `http://localhost:5000`.

2. **Open the Frontend**:
   Simply open the `frontend/index.html` file in your preferred web browser. Alternatively, you can use the provided simple server script in the frontend directory:
   ```bash
   cd frontend
   python server.py
   ```

## How It Works

1. **User Input:** The user types a natural language question (e.g., "List all customers from London") in the frontend UI.
2. **Preprocessing (NLP):** The backend uses NLTK to clean and lemmatize the user's query.
3. **Retrieval (RAG):** The system compares the lemmatized query against all table definitions in `schema.txt` using TF-IDF and Cosine Similarity, isolating the top 3 most relevant tables to save tokens and improve context.
4. **Generation (LLM):** The refined schema and original query are sent to the Google Gemini model using a custom prompt, explicitly asking it to return only valid SQLite code.
5. **Execution (DB):** The generated SQL string is executed safely against the local `northwind.db` SQLite database.
6. **Result Display:** The raw SQL and the resulting datasets are returned as JSON and rendered in the frontend.

## Technologies Used

- **Backend**: Python, Flask, Flask-CORS
- **NLP & RAG**: NLTK (Tokenization, Lemmatization, POS Tagging), Scikit-Learn (TF-IDF, Cosine Similarity)
- **Database**: SQLite3
- **LLM**: Google Generative AI (Gemini 2.5 Flash)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Fetch API)

## License
MIT License
