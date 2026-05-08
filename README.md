# Cognitive-Dialogue-Generation-using-GPT

Backend scaffold for a cognitively-aware dialogue system (FastAPI + PostgreSQL + Alembic).

## Quickstart (dev)

### Option A — Supabase (recommended)

1. In the [Supabase dashboard](https://supabase.com/dashboard): **Project Settings → Database**.
2. Copy the **database password** (not the anon key).
3. Copy `.env.example` to `.env`, set `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_DB_PASSWORD`.

The app builds `DATABASE_URL` as  
`postgresql+asyncpg://postgres:...@db.<project-ref>.supabase.co:5432/postgres`  
(or set `DATABASE_URL` yourself).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_PASSWORD

alembic upgrade head
uvicorn main:app --reload
```

### Option B — Local Postgres (Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

docker run --name cognitive-dialogue-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cognitive_dialogue \
  -p 5432:5432 \
  -d postgres:16

# In .env, set DATABASE_URL or rely on default local URL in config.

alembic upgrade head
uvicorn main:app --reload
```

If you see `database "cognitive_dialogue" does not exist`, either create that database in Postgres or use **Supabase** (database name is `postgres`).

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