# Fantasy Analytics API

The backend API uses FastAPI and Python. The React UI lives in `../fantasy-ui`.

## Requirements

- Python 3.10 or newer

## Run locally

From this directory, create and activate a virtual environment, then install the project:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
fastapi dev app/main.py
```

The API is available at <http://127.0.0.1:8000>. Interactive API docs are at <http://127.0.0.1:8000/docs>.

## Starter endpoints

- `GET /` returns the service name and docs path.
- `GET /health` returns a basic health status.
