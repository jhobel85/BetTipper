import json
from pathlib import Path
from typing import Any

import requests
from sqlalchemy.orm import Session

from ..data_loader import load_matches_from_json, load_teams_from_json, recompute_predictions
from .data_merger import merge_all
from .fbref import get_fbref_stats
from .football_data import RAW_OUTPUT, get_team_recent_matches, save_wc_matches_raw
from .injuries import get_injuries
from .odds import get_odds
from .understat import get_understat

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TEAMS_PATH = DATA_DIR / "teams_ms2026.json"
MATCHES_PATH = DATA_DIR / "matches_ms2026.json"
ELO_TSV_URL = "https://www.eloratings.net/World.tsv"
FIFA_TO_ELO_CODE = {
    "ALG": "DZ",
    "ARG": "AR",
    "AUS": "AU",
    "AUT": "AT",
    "BEL": "BE",
    "BIH": "BA",
    "BRA": "BR",
    "CAN": "CA",
    "CIV": "CI",
    "COD": "CD",
    "COL": "CO",
    "CPV": "CV",
    "CRO": "HR",
    "CUW": "CW",
    "CZE": "CZ",
    "ECU": "EC",
    "EGY": "EG",
    "ENG": "EN",
    "ESP": "ES",
    "FRA": "FR",
    "GER": "DE",
    "GHA": "GH",
    "HAI": "HT",
    "IRN": "IR",
    "IRQ": "IQ",
    "JOR": "JO",
    "JPN": "JP",
    "KOR": "KR",
    "KSA": "SA",
    "MAR": "MA",
    "MEX": "MX",
    "NED": "NL",
    "NOR": "NO",
    "NZL": "NZ",
    "PAN": "PA",
    "PAR": "PY",
    "POR": "PT",
    "QAT": "QA",
    "RSA": "ZA",
    "SCO": "SC",
    "SEN": "SN",
    "SUI": "CH",
    "SWE": "SE",
    "TUN": "TN",
    "TUR": "TR",
    "URY": "UY",
    "USA": "US",
    "UZB": "UZ",
}


def _load_elo_ratings() -> dict[str, float]:
    try:
        response = requests.get(ELO_TSV_URL, timeout=20)
        response.raise_for_status()
    except Exception:
        return {}

    text = response.content.decode("utf-8", errors="ignore")
    ratings: dict[str, float] = {}
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        code = cols[2].strip().upper()
        try:
            elo = float(cols[3].strip())
        except ValueError:
            continue
        if len(code) in {2, 3} and code.isalpha():
            ratings[code] = elo
    return ratings


def _extract_teams_from_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Build basic team performance stats from already finished matches.
    perf: dict[str, dict[str, float]] = {}
    for m in matches:
        status = m.get("status")
        if status != "FINISHED":
            continue

        score = (m.get("score") or {}).get("fullTime") or {}
        home_goals = score.get("home")
        away_goals = score.get("away")
        if home_goals is None or away_goals is None:
            continue

        home_team = m.get("homeTeam") or {}
        away_team = m.get("awayTeam") or {}
        home_code = home_team.get("code") or home_team.get("tla")
        away_code = away_team.get("code") or away_team.get("tla")
        if not home_code or not away_code:
            continue

        perf.setdefault(home_code, {"played": 0.0, "gf": 0.0, "ga": 0.0})
        perf.setdefault(away_code, {"played": 0.0, "gf": 0.0, "ga": 0.0})

        perf[home_code]["played"] += 1.0
        perf[home_code]["gf"] += float(home_goals)
        perf[home_code]["ga"] += float(away_goals)
        perf[away_code]["played"] += 1.0
        perf[away_code]["gf"] += float(away_goals)
        perf[away_code]["ga"] += float(home_goals)

    by_code: dict[str, dict[str, Any]] = {}
    recent_form_cache: dict[int, dict[str, float]] = {}
    elo_ratings = _load_elo_ratings()

    def _recent_form(team_id: int) -> dict[str, float]:
        if team_id in recent_form_cache:
            return recent_form_cache[team_id]
        try:
            recent_matches = get_team_recent_matches(team_id, limit=12)
        except Exception:
            recent_form_cache[team_id] = {"played": 0.0, "gf": 0.0, "ga": 0.0}
            return recent_form_cache[team_id]

        stats = {"played": 0.0, "gf": 0.0, "ga": 0.0}
        for rm in recent_matches:
            score = (rm.get("score") or {}).get("fullTime") or {}
            hg = score.get("home")
            ag = score.get("away")
            if hg is None or ag is None:
                continue
            home_team = rm.get("homeTeam") or {}
            is_home = home_team.get("id") == team_id
            gf = float(hg if is_home else ag)
            ga = float(ag if is_home else hg)
            stats["played"] += 1.0
            stats["gf"] += gf
            stats["ga"] += ga

        recent_form_cache[team_id] = stats
        return stats

    for m in matches:
        for side in ("homeTeam", "awayTeam"):
            team = m.get(side) or {}
            code = team.get("code") or team.get("tla")
            name = team.get("name")
            team_id = team.get("id")
            if not code or not name:
                continue
            if code in by_code:
                continue
            team_perf = perf.get(code, {"played": 0.0, "gf": 0.0, "ga": 0.0})
            played = team_perf["played"]
            if played == 0 and team_id is not None:
                recent = _recent_form(int(team_id))
                if recent["played"] > 0:
                    team_perf = recent
                    played = team_perf["played"]
            if played > 0:
                gf_pg = team_perf["gf"] / played
                ga_pg = team_perf["ga"] / played
                # Center around 1.0 and keep values in sane range for current model.
                rating_attack = max(0.6, min(1.8, 1.0 + (gf_pg - 1.2) * 0.35))
                rating_defense = max(0.6, min(1.8, 1.0 + (1.2 - ga_pg) * 0.35))
                rating_overall = max(1.2, min(3.6, rating_attack + rating_defense))
            else:
                elo_code = FIFA_TO_ELO_CODE.get(code, code)
                elo = elo_ratings.get(elo_code)
                if elo is None:
                    rating_attack = 1.0
                    rating_defense = 1.0
                    rating_overall = 2.0
                else:
                    rating_attack = max(0.6, min(1.8, 1.0 + (elo - 1700.0) / 800.0))
                    rating_defense = max(0.6, min(1.8, 1.0 + (elo - 1700.0) / 900.0))
                    rating_overall = max(1.2, min(3.6, rating_attack + rating_defense))

            by_code[code] = {
                "name": name,
                "fifa_code": code,
                "group": (m.get("group") or "").replace("GROUP_", "") or None,
                "rating_attack": round(rating_attack, 4),
                "rating_defense": round(rating_defense, 4),
                "rating_overall": round(rating_overall, 4),
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
