import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .model import DEFAULT_PARAMS, MatchFeatures, predict_match
from .models import Match, ModelPrediction, Team

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TEAMS_PATH = DATA_DIR / "teams_ms2026.json"
MATCHES_PATH = DATA_DIR / "matches_ms2026.json"
HOST_FIFA_CODES = {"MEX", "USA", "CAN"}


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"Expected JSON array in {path}")
    return payload


def _parse_kickoff(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _safe_float(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed


def _team_overall(team: Team) -> float:
    if team.rating_overall is not None:
        return float(team.rating_overall)
    attack = _safe_float(team.rating_attack, 1.0)
    defense = _safe_float(team.rating_defense, 1.0)
    return attack + defense


def _team_attack(team: Team) -> float:
    return _safe_float(team.rating_attack, 1.0)


def _home_advantage(home_team: Team) -> float:
    if home_team.fifa_code in HOST_FIFA_CODES:
        return 1.0
    return 0.0


def load_teams_from_json(db: Session, path: Path = TEAMS_PATH) -> dict[str, int]:
    rows = _read_json_array(path)
    created = 0
    updated = 0
    skipped = 0

    for row in rows:
        name = str(row.get("name", "")).strip()
        fifa_code = str(row.get("fifa_code", "")).strip()
        if not name:
            skipped += 1
            continue

        team = None
        if fifa_code:
            team = db.query(Team).filter(Team.fifa_code == fifa_code).first()
        if not team:
            team = db.query(Team).filter(Team.name == name).first()

        if not team:
            team = Team(name=name, fifa_code=fifa_code or None)
            db.add(team)
            created += 1
        else:
            updated += 1

        team.group = row.get("group")
        team.rating_attack = row.get("rating_attack")
        team.rating_defense = row.get("rating_defense")
        team.rating_overall = row.get("rating_overall")

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def load_matches_from_json(db: Session, path: Path = MATCHES_PATH) -> dict[str, int]:
    rows = _read_json_array(path)
    created = 0
    updated = 0
    skipped = 0

    for row in rows:
        home_code = str(row.get("home_team_fifa_code") or row.get("home_fifa_code") or "").strip()
        away_code = str(row.get("away_team_fifa_code") or row.get("away_fifa_code") or "").strip()
        kickoff_raw = row.get("kickoff_at")
        stage = row.get("stage")

        if not home_code or not away_code or not kickoff_raw or not stage:
            skipped += 1
            continue

        home_team = db.query(Team).filter(Team.fifa_code == home_code).first()
        away_team = db.query(Team).filter(Team.fifa_code == away_code).first()
        if not home_team or not away_team:
            skipped += 1
            continue

        kickoff_at = _parse_kickoff(str(kickoff_raw))
        match = (
            db.query(Match)
            .filter(
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id,
                Match.kickoff_at == kickoff_at,
            )
            .first()
        )

        if not match:
            match = Match(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                kickoff_at=kickoff_at,
            )
            db.add(match)
            created += 1
        else:
            updated += 1

        match.stage = str(stage)
        match.group = row.get("group")
        match.stadium = row.get("stadium")
        match.status = str(row.get("status") or "scheduled")

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def recompute_predictions(db: Session) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    matches = db.query(Match).all()
    for match in matches:
        home = db.query(Team).filter(Team.id == match.home_team_id).first()
        away = db.query(Team).filter(Team.id == match.away_team_id).first()
        if not home or not away:
            skipped += 1
            continue

        features = MatchFeatures(
            rating_home=_team_overall(home),
            rating_away=_team_overall(away),
            xg_home=_team_attack(home) * 0.9,
            xg_away=_team_attack(away) * 0.9,
            home_advantage=_home_advantage(home),
        )
        result = predict_match(features, DEFAULT_PARAMS)

        prediction = db.query(ModelPrediction).filter(ModelPrediction.match_id == match.id).first()
        if not prediction:
            prediction = ModelPrediction(match_id=match.id)
            db.add(prediction)
            created += 1
        else:
            updated += 1

        prediction.lambda_home = result["lambda_home"]
        prediction.lambda_away = result["lambda_away"]
        prediction.prob_home_win = result["prob_home_win"]
        prediction.prob_draw = result["prob_draw"]
        prediction.prob_away_win = result["prob_away_win"]
        prediction.recommended_outcome = result["recommended_outcome"]
        prediction.confidence_score = result["confidence_score"]

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
