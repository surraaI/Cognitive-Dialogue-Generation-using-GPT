# CogSoc Project Verification Checklist

Run through this checklist to verify the project is fully set up and working.

## Pre-Setup Verification

- [ ] Python 3.11+ installed
- [ ] Docker installed (for containerized setup)
- [ ] OpenAI or Gemini API key available
- [ ] PostgreSQL access (local or Supabase)

## Setup Completion

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `OPENAI_API_KEY` or `GEMINI_API_KEY` set in `.env`
- [ ] Database URL configured (local, Supabase, or docker)
- [ ] Virtual environment created and activated

### Database
- [ ] `alembic upgrade head` run successfully
- [ ] All tables created (users, conversations, messages, user_memory_items)

### Backend Server
- [ ] `uvicorn main:app --reload` starts without errors
- [ ] API accessible at `http://127.0.0.1:8000`
- [ ] Health endpoint returns `{"status":"ok"}`

## API Functionality Tests

### Health Check
```bash
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok"}
```

**Result:** ✅ / ❌

### Chat Endpoint (Socratic Mode)
```bash
USER_ID="11111111-1111-1111-1111-111111111111"
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"'$USER_ID'","message":"What is memory?","mode":"socratic"}'
```

**Expected:** Plain text response with Socratic question
**Result:** ✅ / ❌

### Chat Endpoint (Explanatory Mode)
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"'$USER_ID'","message":"What is memory?","mode":"explanatory"}'
```

**Expected:** Detailed explanation response
**Result:** ✅ / ❌

### Chat Endpoint (Concise Mode)
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"'$USER_ID'","message":"What is memory?","mode":"concise"}'
```

**Expected:** Brief 1-2 sentence response
**Result:** ✅ / ❌

### Memory Endpoint
```bash
curl "http://127.0.0.1:8000/memory?user_id=$USER_ID"
```

**Expected:** JSON with user memory and preferences
**Result:** ✅ / ❌

### Mode Change Endpoint
```bash
curl -X POST http://127.0.0.1:8000/mode \
  -H "Content-Type: application/json" \
  -d '{"user_id":"'$USER_ID'","mode":"socratic"}'
```

**Expected:** Confirmation of mode change
**Result:** ✅ / ❌

## Frontend Tests

### Web UI Access
- [ ] Navigate to `http://127.0.0.1:8000/ui/`
- [ ] Page loads without JavaScript errors

### Header Display
- [ ] Title "CogSoc" visible
- [ ] Subtitle "Socratic Tutor for Cognitive Science" visible
- [ ] Mode selector shows: Explanatory, Socratic (selected), Concise
- [ ] Mode description updates when mode changes

### Chat Functionality
- [ ] Can type message in textarea
- [ ] Send button is clickable
- [ ] Message appears in chat as "You"
- [ ] Assistant response appears within 2-5 seconds
- [ ] Mode is displayed in assistant message

### User Experience
- [ ] Can switch modes and see immediate effect
- [ ] User ID persists across page reloads
- [ ] Conversation ID persists within session
- [ ] Messages scroll to bottom automatically
- [ ] System messages (hints) display correctly

## Component Tests

### Attention Extraction
```python
from app.cognitive.attention import extract_attention
signals = extract_attention("What is working memory?")
# Should have entities, keyphrases, intent, ambiguity_score
```

**Result:** ✅ / ❌

### Prompt Builder
```python
from app.cognitive.prompt_builder import PromptBuilder
from app.cognitive.types import AttentionSignals, MemoryContext, ShortTermMemory, UserProfile
builder = PromptBuilder()
prompt = builder.build(
    user_profile=UserProfile(user_id="test"),
    mode="socratic",
    tone="friendly",
    user_message="What is memory?",
    attention=AttentionSignals(),
    memory=MemoryContext(short_term=ShortTermMemory(recent_turns=[]), long_term=[])
)
# Should return PromptContext with CogSoc system role for socratic mode
```

**Result:** ✅ / ❌

### LLM Adapter
```python
from app.cognitive.llm_adapter import LLMAdapter
adapter = LLMAdapter()
# Requires valid API key in environment
```

**Result:** ✅ / ❌

## Deployment Tests (Optional)

### Docker Build
```bash
docker build -t cogsoc .
```

**Result:** ✅ / ❌

### Docker Compose
```bash
docker-compose up --build
```

**Expected:** Both PostgreSQL and backend start successfully
**Result:** ✅ / ❌

## Documentation Verification

- [ ] README.md is comprehensive and up-to-date
- [ ] SETUP.md covers all installation methods
- [ ] .env.example has helpful comments
- [ ] Code comments explain key functions
- [ ] API response schemas are documented

## Performance Checks

- [ ] Chat response time < 5 seconds (depends on LLM)
- [ ] Multiple conversations can run in parallel
- [ ] No memory leaks after long sessions
- [ ] Database queries are efficient

## Security Checks

- [ ] API keys are in .env (not committed to git)
- [ ] CORS is properly configured
- [ ] Database passwords are strong
- [ ] No sensitive data in logs

## Final Verification

Once all checks pass, the project is ready for:

✅ **Development** — Add new features, experiment with prompts
✅ **Testing** — Run automated tests, manual testing
✅ **Deployment** — Deploy to production (Heroku, Railway, DigitalOcean, etc.)
✅ **Distribution** — Share with users

## Troubleshooting Quick Links

If any test fails, refer to:
- Database issues → SETUP.md "Troubleshooting" section
- API key issues → SETUP.md "Get an LLM API Key" section
- Docker issues → docker-compose.yml and Dockerfile
- Frontend issues → browser console for errors
