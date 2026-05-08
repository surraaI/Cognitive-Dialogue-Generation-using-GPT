# Cognitive-Dialogue-Generation-using-GPT

Backend scaffold for a cognitively-aware dialogue system (FastAPI + PostgreSQL + Alembic).

## Quickstart (dev)

Create a virtualenv, install deps, configure env, run the API:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Database migrations (Alembic)

Set `DATABASE_URL` in `.env`, then:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```