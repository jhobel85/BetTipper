# BetTipper App Usage Guide

This guide shows how to run the app, load real data, and use the main features.

## 1. Start the app (Docker)

From repository root:

```bash
docker-compose down -v
docker-compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API + docs: http://localhost:8000/docs

## 2. Real data loading modes

The backend is configured in `docker-compose.yml` with:

- `BT_AUTO_LOAD_REAL_DATA=true`
- `BT_ENABLE_SAMPLE_SEED=false`

So real data loads automatically on backend startup.

### Required files

You need:
- `backend/data/teams_ms2026.json`
- either:
  - `backend/data/matches_ms2026.json`, or
  - `backend/data/fifa_matches_raw.json` (then `matches_ms2026.json` is generated automatically)

## 3. Auto-fetch full WC 2026 data from providers

You can run provider pipeline to fetch and prepare data:

```bash
curl -X POST http://localhost:8000/api/v1/admin/run-provider-pipeline
```

This pipeline:
1. Downloads WC 2026 matches from football-data.org
2. Writes `backend/data/fifa_matches_raw.json`
3. Produces normalized `backend/data/teams_ms2026.json` and `backend/data/matches_ms2026.json`
4. Imports to DB
5. Recomputes predictions

## 4. Manual admin endpoints (if needed)

```bash
curl -X POST http://localhost:8000/api/v1/admin/load-teams
curl -X POST http://localhost:8000/api/v1/admin/generate-matches
curl -X POST http://localhost:8000/api/v1/admin/load-matches
curl -X POST http://localhost:8000/api/v1/admin/recompute-predictions
```

Also available:
- `POST /api/v1/admin/matches/{match_id}/result` (stores result and recalculates user points)
- `POST /api/v1/admin/update-bookmaker-tips` (refreshes bookmaker tips/odds-based suggestions)
- `POST /api/v1/admin/simulate-tournament?simulations=10000` (Monte-Carlo full tournament simulation)
- `GET /api/v1/admin/group-qualification-probabilities?simulations=10000` (group qualification probabilities)

### OddsPortal source (preferred for bookmaker tips)

Place CSV file at:

- `backend/data/oddsportal_odds.csv`

Supported header variants:
- home: `home` / `home_team` / `team1`
- away: `away` / `away_team` / `team2`
- date: `date` / `match_date` / `kickoff_date` (YYYY-MM-DD recommended)
- odds 1X2:
  - home: `odds_home` / `home_odds` / `odd1` / `1`
  - draw: `odds_draw` / `draw_odds` / `oddx` / `x`
  - away: `odds_away` / `away_odds` / `odd2` / `2`

When available, OddsPortal rows are preferred over football-data odds.

## 5. User flow in web app

1. Open http://localhost:5173
2. Log in (or create account via API docs register endpoint)
3. View matches and model probabilities
4. Submit tips (`1`, `X`, `2`)
5. Check leaderboard

## 6. Auth endpoints

Register:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret","display_name":"Your Name"}'
```

Login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}'
```

## 7. Verify app data quickly

```bash
curl http://localhost:8000/api/v1/matches/
curl http://localhost:8000/api/v1/leaderboard/global
```

If matches are empty, run the provider pipeline endpoint again.

** No positive value edge against model probabilities.
└ That message means there is no value bet for that match under the current model and odds.

  Specifically, for each 1/X/2 outcome, the app computes expected value: EV = model_probability * bookmaker_odds - 1.
  If all EV values are <= 0, it shows: "No positive value edge against model probabilities."

  So the bookmaker prices are not offering a mathematically positive edge versus the model for that fixture.


  └ EV and edge are now clearly defined for your bookmaker opportunity output:

   - EV (Expected Value) uses EV = p_model
    * odds - 1 and estimates long-run return per 1 unit stake.
   - Edge uses Edge = p_model - (1/odds) and measures how much your model probability exceeds bookmaker implied probability.

  For your sample (X, odds 24.00): implied probability is 4.17%; if model is ~25.6%, then edge is +21.4% and EV is +514.8%.