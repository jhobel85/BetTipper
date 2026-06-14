# Copilot Instructions – MS 2026 Tipper (BetTipper)

A FIFA World Cup 2026 tipping app: users register, submit match outcome tips (1/X/2 + optional exact score), and compete on a leaderboard. A Poisson-based model generates match outcome probabilities and a confidence score.

---

## Architecture

Two independent Docker services defined in `docker-compose.yml`:

| Service | Dir | Port | Entry point |
|---------|-----|------|-------------|
| Backend | `backend/` | 8000 | `backend/app/routers/main.py` — FastAPI app |
| Frontend | `frontend/` | 5173 | `frontend/src/main.tsx` — React/Vite |

During development, Vite proxies all `/api` requests to `http://localhost:8000` (configured in `frontend/vite.config.ts`), so frontend fetch calls use `/api/v1/...` with no CORS setup needed locally.

**Backend layers (all under `backend/app/`):**
- `models.py` — SQLAlchemy ORM models (single file for all tables)
- `schemas.py` — Pydantic request/response schemas (separate from ORM models)
- `db.py` — SQLAlchemy engine + `SessionLocal` + `get_db()` dependency
- `prediction.py` — Pure Poisson math (no DB access)
- `routers/` — FastAPI routers, one file per domain (`auth`, `matches`, `tips`, `leaderboard`)
- `routers/main.py` — App factory: creates tables, seeds sample data, mounts routers
- `sample_data.py` — Inserts test teams/matches/predictions at startup

**Database:** SQLite file `ms2026.db` (auto-created at startup in `backend/`). PostgreSQL is the production target; the switch is a one-line change in `db.py`.

---

## Running the App

**Full stack (Docker):**
```bash
docker-compose up --build
```

**Backend only:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload   # Run from backend/ dir
```

**Frontend only:**
```bash
cd frontend
npm install
npm run dev
```

FastAPI interactive docs: http://localhost:8000/docs

---

## Key Conventions

### Backend

- **Imports inside `app/` are always relative.** Use `from ..db import get_db`, `from .. import models, schemas` — never absolute paths like `from app.db`.
- **DB session via dependency injection.** Every router function that needs DB receives `db: Session = Depends(get_db)`. Never instantiate `SessionLocal` directly in a router.
- **ORM models and Pydantic schemas are separate.** Models live in `models.py` (SQLAlchemy), schemas in `schemas.py` (Pydantic). Schemas that serialize ORM objects use `class Config: orm_mode = True`.
- **Router registration pattern.** Each router file sets `router = APIRouter(tags=["..."])`. All routers are mounted in `routers/main.py` with `/api/v1/` prefix.
- **Outcome codes are strings:** `"1"` (home win), `"X"` (draw), `"2"` (away win). These flow from model → DB → API → frontend consistently.
- **Tip upsert:** `POST /matches/{match_id}/tips` creates or updates a tip by `(match_id, user_id)` unique constraint — always check for an existing tip before inserting.
- **No migrations.** Schema is managed via `Base.metadata.create_all(bind=engine)` at startup. For schema changes, drop and recreate the SQLite file locally.

### Frontend

- **API functions are centralized** in `frontend/src/api.ts` with TypeScript types co-located. Add all new `fetch` calls there, not inside components.
- **Components live in `frontend/components/`**, not `frontend/src/components/`.

### Prediction model

- `prediction.py` exports `compute_outcome_probabilities(lambda_home, lambda_away, max_goals=6)`.
- Lambdas are pre-computed from team ratings and stored in the `model_predictions` table alongside each match. The prediction logic is stateless pure Python — no DB dependency.
- Confidence score = `(p_max − p_second) × 100`.

---

## Current Implementation State

- **Auth is a stub.** All routers use `db.query(models.User).first()` — real JWT/session auth is needed before multi-user use.
- **Password hashing uses SHA-256** (`hashlib`) — replace with `bcrypt` or `passlib` before production.
- **No test suite exists** yet. Spec targets `pytest` for the backend.
- **League management** (creating/joining leagues, league leaderboards) is not yet implemented.

---

## Scoring Rules (from spec)

- Correct outcome (1/X/2): **+3 points**
- Correct exact score: **+5 points** (replaces, not adds to, the 3-point outcome score)
- Underdog bonus (implied odds > 3.0 and correct): **+1 bonus point**
- Tiebreaker: total points → number of exact scores → earliest registration
