# Contributing to Relink

## Stack

- **Web**: Next.js 15, TypeScript, Tailwind CSS, localStorage persistence
- **Coach**: FastAPI, Pydantic, provider-pattern LLM router
- **LLM**: Ollama Cloud → Vertex Gemini → mock

## Setup

```bash
# Coach service
cd services/coach
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
export RELINK_LLM_PROVIDER=mock
.venv/bin/uvicorn relink_coach.main:app --port 8787

# Web app
cd apps/web
npm install
export COACH_URL=http://127.0.0.1:8787
npm run dev
```

## Code style

```bash
cd services/coach
ruff check relink_coach tests
ruff format relink_coach tests
mypy relink_coach
pytest -q
```

## Architecture

```
Browser (Next.js)
  ↓
api/coach BFF
  ↓
Coach service
  SafetyGuard (pre-LLM rule classifier)
  Agents (profile, plans, urge, slip, coach, insight, nudge)
  Provider router (ollama → vertex → mock)
  Pydantic response models
```

- Add response models in `relink_coach/models.py` for any new action.
- Keep agents safe-first and avoid medical claims in prompts.
