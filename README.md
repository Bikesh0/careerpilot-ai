# CareerPilot AI

CareerPilot AI is a local Python application for collecting, filtering, and
ranking real job postings, with optional local-Ollama analysis and document
generation.

## Supported Python runtime

The source uses Python 3.10 type-syntax features, so the supported runtime is
Python 3.10 through 3.12. The current workspace was verified with Python
3.12.13. The version contract is declared in `pyproject.toml`.

On this machine, the Windows `py` launcher points to an unavailable Store
Python installation. Use a working Python 3.10–3.12 interpreter to create the
project virtual environment.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements.txt` contains runtime dependencies only. `requirements-dev.txt`
adds pytest for the automated test suite.

## Run the application

```powershell
# CLI daily job agent
.\.venv\Scripts\python.exe main.py

# Flask web application
.\.venv\Scripts\python.exe webapp.py
```

The local AI features require Ollama to be running and a compatible local model
to be installed. The `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, and
`OLLAMA_MAX_TOKENS` environment variables can override the defaults.

## Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite uses fixture-backed mocked HTTP responses and temporary SQLite
databases. It performs no live job searches and does not call Ollama.

## Manual live smoke checks

These are deliberately outside `tests/` and excluded by pytest configuration:

```powershell
# Requires network access and may contact real job boards.
.\.venv\Scripts\python.exe test_sources.py

# Requires a running local Ollama service and an installed model.
.\.venv\Scripts\python.exe app\ai\test_llm.py
```
