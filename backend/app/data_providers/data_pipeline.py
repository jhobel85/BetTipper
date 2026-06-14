import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..data_loader import load_matches_from_json, load_teams_from_json, recompute_predictions
from .data_merger import merge_all
from .fbref import get_fbref_stats
from .football_data import RAW_OUTPUT, save_wc_matches_raw
from .injuries import get_injuries
from .odds import get_odds
from .understat import get_understat

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TEAMS_PATH = DATA_DIR / "teams_ms2026.json"
MATCHES_PATH = DATA_DIR / "matches_ms2026.json"


def _extract_teams_from_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_code: dict[str, dict[str, Any]] = {}

    for m in matches:
        for side in ("homeTeam", "awayTeam"):
            team = m.get(side) or {}
            code = team.get("code") or team.get("tla")
            name = team.get("name")
            if not code or not name:
                continue
            if code in by_code:
                continue
            by_code[code] = {
                "name": name,
                "fifa_code": code,
                "group": (m.get("group") or "").replace("GROUP_", "") or None,
                # Initial baselines until richer provider data is mapped.
                "rating_attack": 1.0,
                "rating_defense": 1.0,
                "rating_overall": 2.0,
            }

    return list(by_code.values())


def _to_matches_json(merged_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in merged_rows:
        home_code = row.get("home_code")
        away_code = row.get("away_code")
        kickoff_at = row.get("kickoff_at")
        stage = row.get("stage")
        if not home_code or not away_code or not kickoff_at or not stage:
            continue

        rows.append(
            {
                "home_team_fifa_code": home_code,
                "away_team_fifa_code": away_code,
                "kickoff_at": kickoff_at,
                "stage": stage,
                "group": row.get("group"),
                "stadium": None,
                "status": "finished" if row.get("status") == "FINISHED" else "scheduled",
            }
        )
    return rows


def run_pipeline(db: Session, season: int = 2026) -> dict[str, Any]:
    source = "remote"
    try:
        raw_payload = save_wc_matches_raw(path=RAW_OUTPUT, season=season)
    except Exception:
        if not RAW_OUTPUT.exists():
            raise RuntimeError(
                "Could not fetch football-data.org matches and no local fallback file exists at "
                f"{RAW_OUTPUT}. Provide FOOTBALL_DATA_API_KEY or create fifa_matches_raw.json."
            )
        with RAW_OUTPUT.open("r", encoding="utf-8") as f:
            raw_payload = json.load(f)
        source = "local_fallback"

    matches = raw_payload.get("matches", [])

    fbref = get_fbref_stats(matches)
    understat = get_understat(matches)
    odds = get_odds(matches)
    injuries = get_injuries(matches)

    merged = merge_all(matches, fbref, understat, odds, injuries)
    teams_json = _extract_teams_from_matches(matches)
    matches_json = _to_matches_json(merged)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with TEAMS_PATH.open("w", encoding="utf-8") as f:
        json.dump(teams_json, f, indent=2, ensure_ascii=False)
    with MATCHES_PATH.open("w", encoding="utf-8") as f:
        json.dump(matches_json, f, indent=2, ensure_ascii=False)

    teams_result = load_teams_from_json(db, path=TEAMS_PATH)
    matches_result = load_matches_from_json(db, path=MATCHES_PATH)
    prediction_result = recompute_predictions(db)

    return {
        "season": season,
        "source": source,
        "raw_matches": len(matches),
        "merged_rows": len(merged),
        "teams_file_count": len(teams_json),
        "matches_file_count": len(matches_json),
        "providers": {
            "fbref_records": len(fbref),
            "understat_records": len(understat),
            "odds_records": len(odds),
            "injury_records": len(injuries),
        },
        "db": {
            "teams": teams_result,
            "matches": matches_result,
            "predictions": prediction_result,
        },
    }
