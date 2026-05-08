# Cognitive-Dialogue-Generation-using-GPT

Backend scaffold for a cognitively-aware dialogue system (FastAPI + PostgreSQL + Alembic).

## Quickstart (dev)

Create a virtualenv, install deps, configure env, run PostgreSQL, apply migrations, start the API:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start Postgres (Docker)
docker run --name cognitive-dialogue-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cognitive_dialogue \
  -p 5432:5432 \
  -d postgres:16

# Run migrations
alembic upgrade head

# Start API
uvicorn main:app --reload
```

## Database migrations (Alembic)

Set `DATABASE_URL` in `.env`, then:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Check the API (terminal)

```bash
curl -s http://127.0.0.1:8000/health
```

```bash
# Replace USER_ID with any UUID (example below)
USER_ID="11111111-1111-1111-1111-111111111111"

curl -s -X POST http://127.0.0.1:8000/chat \
  -H "content-type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"Switch to Socratic mode and help me design memory.\"}"
```

```bash
curl -s "http://127.0.0.1:8000/memory?user_id=$USER_ID"
```