# Fairy Tales Bias Analysis

A small Flask web app that analyzes public-domain fairy tales for bias using spaCy and TextBlob. It reports:
- Gender balance (mentions/pronouns)
- Role diversity (variety of roles across characters)
- Stereotype signals (penalties for stereotypical language)

The UI is a simple form: paste a story URL, and the app returns a readable textual report.

## Features
- Flask backend (`app.py`) with a single Analyze endpoint (POST → redirects to home)
- Reuses your existing `fairy_tales_without_bias_1.py` analysis logic
- Frontend: clean, responsive layout (HTML + CSS only)
- Matplotlib is forced to a non-interactive backend; `plt.show()` is a no-op so the server won’t block

## Requirements
The app uses Python 3.12 (recommended) and the following packages (see `requirements.txt`):

```
flask
spacy
textblob
pandas
matplotlib
gunicorn
```

You’ll also need the spaCy model:

```
python -m spacy download en_core_web_sm
```

## Local setup (Windows PowerShell)

```powershell
# 1) Create and activate a virtual environment (Python 3.12)
python -m venv venv
.\venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3) Run the app (development)
set FLASK_APP=app.py
set FLASK_ENV=development
python app.py

# The app starts on http://127.0.0.1:5000
```

Notes
- If you previously used Python 3.14 and had trouble installing spaCy on Windows, prefer Python 3.12 where prebuilt wheels are available.

## How it works
- The Flask route lazily imports `fairy_tales_without_bias_1.py` to avoid heavy imports on startup.
- The analysis function `analyze_book_from_url(url, title)` returns a dict of metrics.
- The server formats those metrics into a readable report and renders it on the home page.
- The app uses a Post/Redirect/Get flow so page refresh returns to a clean home.

## Deploy options
Pick any of the below based on effort, cost, and scaling needs.

- Render (easy):
  - Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
  - Start command: `gunicorn app:app`
- Railway/Zeet/Northflank: similar to Render. Set start: `gunicorn app:app --timeout 120`.
- PythonAnywhere: install deps + model in the console; point WSGI to `app:app`.
- Fly.io / Cloud Run (Docker): use the Dockerfile snippet below.

### Dockerfile (example)
```Dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libglib2.0-0 libgl1-mesa-glx curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

COPY . .
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "3", "--threads", "2"]
```

## Health check (optional)
Add a simple route to confirm the app is alive:

```python
@app.get('/health')
def health():
    return {"status": "ok"}, 200
```

## Troubleshooting
- If the app crashes on import due to matplotlib, make sure `matplotlib.use('Agg')` is set before importing pyplot (already handled in `app.py`).
- If spaCy fails to install on Windows, use Python 3.12 and upgrade pip/setuptools/wheel, then reinstall.
- If external URLs are slow or blocked, try another story URL or add a request timeout around the fetch in the analysis.

