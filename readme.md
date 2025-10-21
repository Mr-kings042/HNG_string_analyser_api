
# String Analysis API

A RESTFUL FastAPI service that stores and analyzes strings. It computes properties such as length, whether the string is a palindrome, word count, character frequency, and a SHA256 id. The API allows creating string analyses, fetching single entries, filtering by structured query parameters, filtering by simple natural-language queries, listing all entries, and deleting entries.

## Quick features
- Create string analysis: POST /strings
- Retrieve single string: GET /strings/{string_value}
- Filter strings: GET /strings with query params
- Natural-language filtering: GET /strings/filter-by-natural-language?query=...
- Delete string: DELETE /strings/{string_value}

## Contents

- `main.py` - application entry (FastAPI app)
- `routes.py` - API routes and request handlers
- `services.py` - business logic (string analysis, filtering, natural-language parsing)
- `models.py` - SQLAlchemy models (Strings)
- `schema.py` - Pydantic request/response schemas
- `database.py` - database session / engine setup
- `middleware.py` - request id and timing middleware
- `logger.py` - logging helper
- `test_app.py` - tests (if present)

## Quick start — prerequisites

- Python 3.10 or newer
- A running database (Postgres recommended) or SQLite for local/dev
- Git (optional)

## Install dependencies

Create a virtual environment and install required packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you don't have a `requirements.txt`, here are the primary packages to install:

```powershell
python -m pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
# If using PostgreSQL
python -m pip install psycopg2-binary
```

## Environment

Create a `.env` file in the project root with at least the database connection string. Example using PostgreSQL:

```
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/string_db
```

For a simple local developer setup you may use SQLite by setting `DATABASE_URL=sqlite:///./dev.db`.

## Run locally

Start the app with Uvicorn (from the repository root):

```powershell
uvicorn main:app --reload --port 8000
```

Open the interactive API docs at: http://127.0.0.1:8000/docs

Open the OpenAPI JSON at: http://127.0.0.1:8000/openapi.json

## API Documentation

Base path: `/strings`

1) Create string
- Method: POST
- Path: `/strings/`
- Request body (JSON):

```json
{
	"value": "some string"
}
```

- Success (201 Created):

```json
{
	"id": "sha256_hash_value",
	"value": "some string",
	"properties": { /* StringProperties */ },
	"created_at": "2025-08-27T10:00:00Z"
}
```

- Errors:
	- 400 Bad Request — missing or invalid `value`
	- 409 Conflict — string already exists

2) Get single string
- Method: GET
- Path: `/strings/{string_value}`
- Success (200 OK):

```json
{
	"id": "sha256_hash_value",
	"value": "requested string",
	"properties": { /* StringProperties */ },
	"created_at": "2025-08-27T10:00:00Z"
}
```

- Error: 404 Not Found — string does not exist

3) Get all strings with filtering
- Method: GET
- Path: `/strings`
- Query parameters:
	- `is_palindrome`: boolean (true/false)
	- `min_length`: integer (minimum string length)
	- `max_length`: integer (maximum string length)
	- `word_count`: integer (exact word count)
	- `contains_character`: string (single character)

- Example:
	`/strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a`

- Success (200 OK) response shape:

```json
{
	"data": [
		{
			"id": "hash1",
			"value": "string1",
			"properties": { /* StringProperties */ },
			"created_at": "2025-08-27T10:00:00Z"
		}
	],
	"count": 1,
	"filters_applied": {
		"is_palindrome": true,
		"min_length": 5,
		"max_length": 20,
		"word_count": 2,
		"contains_character": "a"
	}
}
```

- Errors: 400 Bad Request — invalid query parameter values or types

4) Natural language filtering
- Method: GET
- Path: `/strings/filter-by-natural-language?query=<urlencoded query>`
- Example queries supported (heuristics):
	- "all single word palindromic strings" → { "word_count": 1, "is_palindrome": true }
	- "strings longer than 10 characters" → { "min_length": 11 }
	- "palindromic strings that contain the first vowel" → { "is_palindrome": true, "contains_character": "a" } (heuristic)
	- "strings containing the letter z" → { "contains_character": "z" }

- Success (200 OK):

```json
{
	"data": [ /* array of matching strings */ ],
	"count": 3,
	"interpreted_query": {
		"original": "all single word palindromic strings",
		"parsed_filters": {
			"word_count": 1,
			"is_palindrome": true
		}
	}
}
```

- Errors:
	- 400 Bad Request — unable to parse natural language query
	- 422 Unprocessable Entity — query parsed but filters conflict (e.g., min_length > max_length)

5) Delete string
- Method: DELETE
- Path: `/strings/{string_value}`
- Success: 204 No Content
- Error: 404 Not Found — string does not exist

## Examples (curl / PowerShell)

Create:
```powershell
curl -X POST "http://127.0.0.1:8000/strings/" -H "Content-Type: application/json" -d '{"value":"racecar"}'
```

Filter:
```powershell
curl "http://127.0.0.1:8000/strings?is_palindrome=true&min_length=3"
```

Natural language:
```powershell
curl "http://127.0.0.1:8000/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings"
```

## Testing

 run tests with pytest:

```powershell
python -m pip install pytest
pytest -q
```
