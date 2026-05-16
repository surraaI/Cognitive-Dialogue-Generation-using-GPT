# CogSoc Setup Guide

A complete guide to setting up and running the Socratic tutor for cognitive science.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized setup)
- An LLM API key (OpenAI or Google Gemini)
- PostgreSQL (or Supabase account for cloud database)

## Step 1: Clone and Install Dependencies

```bash
git clone <repository-url>
cd Cognitive-Dialogue-Generation-using-GPT

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

### Option A: Local PostgreSQL

```bash
# .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cognitive_dialogue
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your-key-here
```

Start PostgreSQL locally:

```bash
docker run --name cognitive-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cognitive_dialogue \
  -p 5432:5432 \
  -d postgres:16
```

### Option B: Supabase (Cloud)

1. Create a free account at [https://supabase.com](https://supabase.com)
2. Create a new project
3. Get credentials from **Project Settings → Database**:
   - `SUPABASE_URL`: From **Settings → API → Project URL**
   - `SUPABASE_KEY`: From **Settings → API → anon key**
   - `SUPABASE_DB_PASSWORD`: From **Settings → Database** (the database password shown once)

```bash
# .env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-database-password
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

### Option C: Docker Compose (All-in-One)

```bash
# .env - just set your LLM key
OPENAI_API_KEY=sk-your-key-here
```

Then:

```bash
docker-compose up --build
```

This automatically starts PostgreSQL and the backend.

## Step 3: Get an LLM API Key

### OpenAI

1. Visit [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env`:

```bash
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini  # or gpt-4 for better quality
```

### Google Gemini

1. Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`:

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your-key-here
```

## Step 4: Run Database Migrations

```bash
alembic upgrade head
```

This creates the necessary tables (users, conversations, messages, memory items).

## Step 5: Start the Server

```bash
uvicorn main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 6: Open the Web Interface

Visit: **[http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/)**

## Testing the API

### Health Check

```bash
curl http://127.0.0.1:8000/health
# Response: {"status":"ok"}
```

### Send a Message

```bash
USER_ID="11111111-1111-1111-1111-111111111111"

curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "message": "What is memory?",
    "mode": "socratic"
  }'
```

### Get User Memory

```bash
curl "http://127.0.0.1:8000/memory?user_id=$USER_ID"
```

## Architecture

```
CogSoc
├── Frontend (HTML/CSS/JS)
│   └── Real-time chat interface with mode selection
├── Backend (FastAPI + PostgreSQL)
│   ├── API Routes
│   │   ├── /chat (POST) — Send messages
│   │   ├── /memory (GET) — Retrieve user memory
│   │   └── /mode (POST) — Change dialogue mode
│   ├── Cognitive Pipeline
│   │   ├── Attention Extraction — Extract entities/keyphrases
│   │   ├── Memory Manager — Build context from history
│   │   ├── Prompt Builder — Construct LLM prompts
│   │   ├── LLM Adapter — Call OpenAI/Gemini
│   │   └── Summarizer — Create conversation summaries
│   └── Database
│       ├── Users
│       ├── Conversations
│       ├── Messages
│       └── User Memory Items
```

## Dialogue Modes

### 🤔 Socratic Mode (Default)

Asks guiding questions to help students discover insights themselves:

```
User: "What is memory?"
CogSoc: "Great question! Have you ever tried to remember a phone number just long enough to dial it?"
```

### 📖 Explanatory Mode

Provides detailed explanations with concrete examples:

```
User: "What is memory?"
CogSoc: "Memory is the cognitive ability to encode, store, and retrieve information. 
It involves three main types: sensory memory, short-term/working memory, and long-term memory..."
```

### ⚡ Concise Mode

Brief, to-the-point answers:

```
User: "What is memory?"
CogSoc: "The ability to encode, store, and retrieve information."
```

## Troubleshooting

### "Connection refused" — PostgreSQL not running

Start PostgreSQL:

```bash
docker run --name cognitive-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cognitive_dialogue \
  -p 5432:5432 \
  -d postgres:16
```

### "API key not set" — LLM won't respond

Check your `.env`:

```bash
OPENAI_API_KEY=sk-...  # Must start with sk-
```

### "Database URL is invalid"

Make sure your `DATABASE_URL` is correct:

```bash
# Local: postgresql+asyncpg://postgres:PASSWORD@localhost:5432/DB_NAME
# Supabase: postgresql+asyncpg://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

### Migrations failed

Reset your database:

```bash
alembic downgrade base  # Remove all migrations
alembic upgrade head    # Reapply migrations
```

## Development

### Run Tests

```bash
pytest
```

### Run Linter

```bash
ruff check app/
```

### Create a New Migration

```bash
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## Deployment

### Deploy to Heroku

```bash
git push heroku main
heroku run alembic upgrade head
```

### Deploy to Railway.app

```bash
railway link
railway up
```

### Deploy to DigitalOcean App Platform

```bash
doctl apps create --spec app.yaml
```

## API Reference

### POST /chat

Send a message and get a tutored response.

**Request:**

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "conversation_id": "22222222-2222-2222-2222-222222222222",  // optional
  "message": "What is memory?",
  "mode": "socratic",  // socratic, explanatory, concise
  "tone": "friendly",   // optional
  "metadata": {}        // optional
}
```

**Response:**

```json
{
  "conversation_id": "22222222-2222-2222-2222-222222222222",
  "assistant_message": "Have you ever tried to remember something and forgotten it? That's the key...",
  "mode": "socratic",
  "tone": "friendly",
  "attention": {
    "entities": [{"text": "memory", "score": 0.8}],
    "keyphrases": [{"text": "memory concept", "score": 0.6}],
    "ambiguity_score": 0.1
  },
  "memory_updates": [
    {"key": "pref:mode", "action": "upsert", "confidence": 0.8}
  ]
}
```

### GET /memory

Retrieve user memory and preferences.

**Query Parameters:**

- `user_id` (required): UUID

**Response:**

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "short_term": {
    "summary": "Recent conversation about memory and attention",
    "recent_turns": [...]
  },
  "long_term": [
    {
      "key": "pref:mode",
      "value": {"mode": "socratic"},
      "confidence": 0.9,
      "importance": 0.8
    }
  ]
}
```

### POST /mode

Change dialogue mode for a conversation or user default.

**Request:**

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "conversation_id": "22222222-2222-2222-2222-222222222222",  // optional
  "mode": "explanatory",
  "tone": "instructional"  // optional
}
```

## License

MIT License — See LICENSE file

## Support

For issues, questions, or feature requests, please open a GitHub issue.
