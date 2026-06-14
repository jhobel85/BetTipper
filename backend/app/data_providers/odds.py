import csv
import re
import unicodedata
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ODDSPORTAL_CSV_PATH = DATA_DIR / "oddsportal_odds.csv"


def _normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    return normalized


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    try:
        parsed = float(text)
    except ValueError:
        return None
    if parsed <= 0:
        return None
    return parsed


def _load_oddsportal_csv(path: Path = ODDSPORTAL_CSV_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="ignore")
    delimiter = ";" if text.count(";") > text.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return [dict(row) for row in reader if row]


def get_oddsportal_file_info(path: Path = ODDSPORTAL_CSV_PATH) -> dict[str, int | bool]:
    exists = path.exists()
    if not exists:
        return {"exists": False, "size_bytes": 0, "rows": 0}
    size_bytes = path.stat().st_size
    rows = len(_load_oddsportal_csv(path))
    return {"exists": True, "size_bytes": int(size_bytes), "rows": int(rows)}


def _extract_csv_value(row: dict[str, str], keys: list[str]) -> str | None:
    lowered = {k.lower(): v for k, v in row.items() if k}
    for key in keys:
        value = lowered.get(key.lower())
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def _odds_from_football_data(match_data: list[dict[str, Any]]) -> dict[int, dict[str, float | str]]:
    out: dict[int, dict[str, float | str]] = {}
    for m in match_data:
        match_id = m.get("id")
        odds = m.get("odds") or {}
        if not match_id or not odds:
            continue
        home = _parse_float(odds.get("homeWin"))
        draw = _parse_float(odds.get("draw"))
        away = _parse_float(odds.get("awayWin"))
        if home is None or draw is None or away is None:
            continue
        out[int(match_id)] = {"home": home, "draw": draw, "away": away, "source": "football-data"}
    return out


def _odds_from_oddsportal(
    match_data: list[dict[str, Any]], path: Path = ODDSPORTAL_CSV_PATH
) -> dict[int, dict[str, float | str]]:
    rows = _load_oddsportal_csv(path)
    if not rows:
        return {}

    by_key: dict[tuple[str, str, str], dict[str, float | str]] = {}
    for row in rows:
        home = _extract_csv_value(row, ["home", "home_team", "team1"])
        away = _extract_csv_value(row, ["away", "away_team", "team2"])
        date = _extract_csv_value(row, ["date", "match_date", "kickoff_date"])
        odds_home = _parse_float(_extract_csv_value(row, ["odds_home", "home_odds", "odd1", "1"]))
        odds_draw = _parse_float(_extract_csv_value(row, ["odds_draw", "draw_odds", "oddx", "x"]))
        odds_away = _parse_float(_extract_csv_value(row, ["odds_away", "away_odds", "odd2", "2"]))
        if not home or not away or not date or odds_home is None or odds_draw is None or odds_away is None:
            continue
        key = (_normalize_name(home), _normalize_name(away), date[:10])
        by_key[key] = {
            "home": odds_home,
            "draw": odds_draw,
            "away": odds_away,
            "source": "oddsportal",
        }

    out: dict[int, dict[str, float | str]] = {}
    for m in match_data:
        match_id = m.get("id")
        if not match_id:
            continue
        home = (m.get("homeTeam") or {}).get("name")
        away = (m.get("awayTeam") or {}).get("name")
        date = str(m.get("utcDate") or "")[:10]
        if not home or not away or not date:
            continue
        key = (_normalize_name(home), _normalize_name(away), date)
        odds = by_key.get(key)
        if odds:
            out[int(match_id)] = odds
    return out


def get_odds(match_data: list[dict[str, Any]] | None = None) -> dict[int, dict[str, float | str]]:
    """
    Resolve odds by match id, preferring OddsPortal CSV data when available.
    Returns {match_id: {"home": float, "draw": float, "away": float, "source": str}}
    """
    if not match_data:
        return {}

    football_data_odds = _odds_from_football_data(match_data)
    oddsportal_odds = _odds_from_oddsportal(match_data)

    # Prefer OddsPortal rows when present.
    merged = dict(football_data_odds)
    merged.update(oddsportal_odds)
    return merged
