# MS 2026 Tipper – Specification

Author: Josef  
Version: 0.1  
Date: TBD  

---

## 1. Overview

**Project:** Web application for tipping FIFA World Cup 2026 matches.  
**Primary purpose:**  
- Fun tipper for friends/colleagues.  
- Optional analytical layer (model probabilities, “confidence”, light value hints).

**Core idea:**  
- Users tip match outcomes (1X2, optionally exact score).  
- System computes its own probabilities using a simple model (Poisson/Dixon–Coles style).  
- Leaderboards rank users by performance across the tournament.

---

## 2. Goals and non‑goals

### 2.1 Goals

- **G1:** Allow users to register/login and join tip competitions (global + private leagues).
- **G2:** Provide full match list for MS 2026 (groups + knockout).
- **G3:** Allow tipping:
  - 1X2 (mandatory)
  - Exact score (optional)
- **G4:** Compute and display:
  - Model probabilities for 1/X/2.
  - Recommended tip + confidence score.
- **G5:** Score users’ tips and show leaderboards.
- **G6:** Keep architecture simple, readable, and Copilot‑friendly.

### 2.2 Non‑goals (v1)

- No real‑money betting integration.
- No live odds scraping in v1 (odds can be added later).
- No full mobile app (responsive web is enough).
- No multi‑sport support (only MS 2026).

---

## 3. User roles and flows

### 3.1 Roles

- **Guest**
  - View public match list and model predictions.
- **Registered user**
  - Create/edit tips.
  - Join/leave leagues.
  - View own stats and leaderboards.
- **Admin**
  - Manage teams, matches, results.
  - Trigger model recalculation if needed.

### 3.2 Key flows

- **F1: Registration & login**
  - Email + password (or OAuth later).
- **F2: Browse matches**
  - Filter by date, group, stage.
- **F3: Create/edit tip**
  - Before match kickoff only.
- **F4: View model prediction**
  - For each match: P(1), P(X), P(2), recommended tip, confidence.
- **F5: View leaderboard**
  - Global leaderboard.
  - League‑specific leaderboard.
- **F6: Admin result entry**
  - Enter final score → system recalculates points.

---

## 4. Scoring rules

### 4.1 Basic scoring

- **Correct outcome (1X2):** +3 points.
- **Correct exact score:** +5 points total (not 3+5, just 5).
- **Optional bonus:**  
  - If user tipped underdog (e.g. implied odds > 3.0) and was correct → +1 bonus.

### 4.2 Tie‑breaking

- 1st: Total points.  
- 2nd: Number of exact scores.  
- 3rd: Earliest registration time (or random).

---

## 5. Data model (conceptual)

### 5.1 Entities

- **User**
  - id, email, password_hash, display_name, created_at
- **League**
  - id, name, description, owner_user_id, created_at
- **LeagueMembership**
  - id, league_id, user_id, role (member/admin)
- **Team**
  - id, name, fifa_code, group, rating_attack, rating_defense, rating_overall
- **Match**
  - id, home_team_id, away_team_id, kickoff_at, stage, group, stadium, status
  - result_home_goals, result_away_goals (nullable until played)
- **ModelPrediction**
  - id, match_id
  - lambda_home, lambda_away
  - prob_home_win, prob_draw, prob_away_win
  - recommended_outcome (1/X/2)
  - confidence_score (0–100)
- **Tip**
  - id, match_id, user_id
  - predicted_outcome (1/X/2)
  - predicted_home_goals, predicted_away_goals (optional)
  - created_at, updated_at
- **TipScore**
  - id, tip_id
  - points_outcome, points_exact, points_bonus
  - total_points

---

## 6. Database schema (relational draft)

> Target: PostgreSQL (or SQLite for dev).

### 6.1 Tables

```sql
CREATE TABLE users (
  id              SERIAL PRIMARY KEY,
  email           TEXT UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  display_name    TEXT NOT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE leagues (
  id              SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  description     TEXT,
  owner_user_id   INTEGER NOT NULL REFERENCES users(id),
  created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE league_memberships (
  id              SERIAL PRIMARY KEY,
  league_id       INTEGER NOT NULL REFERENCES leagues(id),
  user_id         INTEGER NOT NULL REFERENCES users(id),
  role            TEXT NOT NULL DEFAULT 'member'
);

CREATE TABLE teams (
  id              SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  fifa_code       TEXT,
  "group"         TEXT,
  rating_attack   REAL,
  rating_defense  REAL,
  rating_overall  REAL
);

CREATE TABLE matches (
  id                  SERIAL PRIMARY KEY,
  home_team_id        INTEGER NOT NULL REFERENCES teams(id),
  away_team_id        INTEGER NOT NULL REFERENCES teams(id),
  kickoff_at          TIMESTAMP NOT NULL,
  stage               TEXT NOT NULL,
  "group"             TEXT,
  stadium             TEXT,
  status              TEXT NOT NULL DEFAULT 'scheduled',
  result_home_goals   INTEGER,
  result_away_goals   INTEGER
);

CREATE TABLE model_predictions (
  id                  SERIAL PRIMARY KEY,
  match_id            INTEGER NOT NULL REFERENCES matches(id) UNIQUE,
  lambda_home         REAL NOT NULL,
  lambda_away         REAL NOT NULL,
  prob_home_win       REAL NOT NULL,
  prob_draw           REAL NOT NULL,
  prob_away_win       REAL NOT NULL,
  recommended_outcome TEXT NOT NULL,
  confidence_score    REAL NOT NULL
);

CREATE TABLE tips (
  id                  SERIAL PRIMARY KEY,
  match_id            INTEGER NOT NULL REFERENCES matches(id),
  user_id             INTEGER NOT NULL REFERENCES users(id),
  predicted_outcome   TEXT NOT NULL,
  predicted_home_goals INTEGER,
  predicted_away_goals INTEGER,
  created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (match_id, user_id)
);

CREATE TABLE tip_scores (
  id                  SERIAL PRIMARY KEY,
  tip_id              INTEGER NOT NULL REFERENCES tips(id) UNIQUE,
  points_outcome      INTEGER NOT NULL DEFAULT 0,
  points_exact        INTEGER NOT NULL DEFAULT 0,
  points_bonus        INTEGER NOT NULL DEFAULT 0,
  total_points        INTEGER NOT NULL DEFAULT 0
);

# 7. Prediction Model (Poisson)

## 7.1 Inputs

- Team attack rating  
- Team defense rating  
- Home advantage constant  
- Optional tuning parameters  
- Ratings derived from qualification, friendlies, Elo/SPI, or manual calibration  

## 7.2 Expected Goals

Expected goals are computed using exponential functions of attack/defense strength:



\[
\lambda_{home} = \exp(\alpha + A_{home} - D_{away})
\]





\[
\lambda_{away} = \exp(\beta + A_{away} - D_{home})
\]



Where:  
- \(A_{team}\) = attack rating  
- \(D_{team}\) = defense rating  
- \(\alpha, \beta\) = intercepts (home/away advantage)  

## 7.3 Outcome Probabilities

Goals are assumed to follow independent Poisson distributions.

For goals \(k, l \in [0, 6]\):



\[
P(G_{home}=k) = \frac{\lambda_{home}^k e^{-\lambda_{home}}}{k!}
\]





\[
P(G_{away}=l) = \frac{\lambda_{away}^l e^{-\lambda_{away}}}{l!}
\]



Outcome probabilities:

- **Home win:**  
  

\[
  P(1) = \sum_{k>l} P(k,l)
  \]



- **Draw:**  
  

\[
  P(X) = \sum_{k=l} P(k,l)
  \]



- **Away win:**  
  

\[
  P(2) = \sum_{k<l} P(k,l)
  \]



## 7.4 Confidence Score

Let \(p_1, p_X, p_2\) be the outcome probabilities.



\[
confidence = (p_{max} - p_{second}) \times 100
\]



Recommended outcome = argmax of \(p_1, p_X, p_2\).

---

# 8. API Specification (FastAPI‑style)

Base URL: `/api/v1`

## 8.1 Auth

### POST /auth/register  
Body: `{ email, password, display_name }`  
Returns: user + token  

### POST /auth/login  
Body: `{ email, password }`  
Returns: user + token  

---

## 8.2 Matches

### GET /matches  
Query params: `date`, `stage`, `group`  
Returns: list of matches + model predictions  

### GET /matches/{match_id}  
Returns: match detail, model prediction, user tip (if logged in)  

---

## 8.3 Tips

### POST /matches/{match_id}/tips  
Body: `{ predicted_outcome, predicted_home_goals?, predicted_away_goals? }`  
Creates or updates a tip  

### GET /users/me/tips  
Returns: all user tips + scores  

---

## 8.4 Leaderboards

### GET /leaderboard/global  
Returns: global ranking  

### GET /leagues/{league_id}/leaderboard  
Returns: ranking inside league  

---

## 8.5 Admin

### POST /admin/matches/{match_id}/result  
Body: `{ result_home_goals, result_away_goals }`  
Triggers recalculation of all tip scores  

---

# 9. Frontend Structure

## 9.1 Pages

- Login / Register  
- Match List  
- Match Detail  
- My Tips  
- Leaderboards  
- League Management  

## 9.2 Components

- `MatchCard`  
- `PredictionBadge`  
- `TipForm`  
- `LeaderboardTable`  
- `LeagueJoinDialog`  

---

# 10. Tech Stack

## Backend

- Python 3.11+  
- FastAPI  
- SQLAlchemy or SQLModel  
- PostgreSQL (production)  
- SQLite (development)  
- pytest for testing  

## Frontend

- React + TypeScript  
- MUI or minimal custom UI  
- Vite or Next.js  

## Deployment

- Docker containers  
- VPS (Hetzner / DigitalOcean)  
- Nginx reverse proxy  

---

# 11. Backend Project Structure - Backend Skeleton (FastAPI + SQLModel)
backend/
app/
main.py
api/
v1/
auth.py
matches.py
tips.py
leaderboard.py
admin.py
core/
config.py
security.py
models/
user.py
league.py
team.py
match.py
prediction.py
tip.py
schemas/
auth.py
match.py
tip.py
leaderboard.py
services/
prediction_service.py
scoring_service.py
db/
base.py
session.py
init_data.py
tests/


---

# 12. Copilot‑Friendly Prompts

## Models

- “Generate SQLModel classes for tables in SPEC.md section 6.”  
- “Implement Poisson prediction in `prediction_service.py`.”  

## API

- “Create FastAPI router for `/matches` with list + detail endpoints.”  
- “Implement `/matches/{id}/tips` with upsert logic.”  

from fastapi import FastAPI
from app.api.v1 import auth, matches, tips, leaderboard, admin

app = FastAPI(title="MS 2026 Tipper API")

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(matches.router, prefix="/api/v1/matches")
app.include_router(tips.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin")

## Scoring

- “Implement scoring logic from SPEC.md section 4.”  

# 3. Frontend Skeleton (React + TypeScript)

- “Create React component `MatchList` that fetches `/api/v1/matches`.”  
- “Create `TipForm` that posts to `/matches/{id}/tips`.”  

frontend/
src/
api/
auth.ts
matches.ts
tips.ts
leaderboard.ts
components/
MatchCard.tsx
PredictionBadge.tsx
TipForm.tsx
LeaderboardTable.tsx
LeagueJoinDialog.tsx
pages/
LoginPage.tsx
RegisterPage.tsx
MatchListPage.tsx
MatchDetailPage.tsx
MyTipsPage.tsx
LeaderboardPage.tsx
LeaguePage.tsx
hooks/
useAuth.ts
layout/
AppLayout.tsx
App.tsx
main.tsx
public/
index.html
package.json
tsconfig.json
vite.config.ts

## Database

- “Write Alembic migration for schema in SPEC.md.”  

---

# 13. Future Extensions

- Odds integration (Tipsport, Fortuna, Pinnacle).  
- Value betting hints (EV > 0).  
- Group progression simulation.  
- Team dashboards (form, xG, momentum).  
- Multi‑language (CZ/EN).  
- Mobile PWA mode.  

---

