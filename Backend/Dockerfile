# FastAPI backend. Build context must be the Backend/ directory.
FROM python:3.13-slim

WORKDIR /app

# Install deps first so this layer is cached across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# docker-entrypoint.py creates the schema + seeds demo data on a fresh
# database (see its docstring for why this isn't a plain `alembic upgrade
# head`), then this starts the API. No --reload here — that's a dev-only
# convenience.
#
# ${PORT:-8000}: Render assigns its own port via $PORT (observed: 10000)
# and expects the app to bind to it -- hardcoding 8000 made Render fall
# back to auto-detecting the actual port and restarting the deploy to
# correct its routing. Defaults to 8000 for local/Docker Compose use,
# where nothing sets $PORT.
CMD ["sh", "-c", "python docker-entrypoint.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
