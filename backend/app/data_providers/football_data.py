import json
import os
from pathlib import Path
from typing import Any

import requests

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_OUTPUT = DATA_DIR / "fifa_matches_raw.json"


def get_wc_matches_raw(season: int = 2026) -> dict[str, Any]:
    url = f"{BASE_URL}/competitions/WC/matches"
    response = requests.get(
        url,
        headers={"X-Auth-Token": API_KEY},
        params={"season": season},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def save_wc_matches_raw(path: Path = RAW_OUTPUT, season: int = 2026) -> dict[str, Any]:
    payload = get_wc_matches_raw(season=season)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def get_matches(season: int = 2026) -> list[dict[str, Any]]:
    payload = get_wc_matches_raw(season=season)
    return payload.get("matches", [])