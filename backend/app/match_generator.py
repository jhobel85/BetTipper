import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_FIFA_RAW_PATH = DATA_DIR / "fifa_matches_raw.json"
DEFAULT_OUTPUT_PATH = DATA_DIR / "matches_ms2026.json"


def generate_matches_from_fifa_api(
    fifa_json_path: Path = DEFAULT_FIFA_RAW_PATH, output_path: Path = DEFAULT_OUTPUT_PATH
) -> int:
    with fifa_json_path.open("r", encoding="utf-8") as f:
        fifa_data = json.load(f)

    matches = []

    for m in fifa_data["matches"]:
        home_team = m.get("homeTeam", {})
        away_team = m.get("awayTeam", {})
        matches.append({
            "home_fifa_code": home_team.get("code") or home_team.get("tla"),
            "away_fifa_code": away_team.get("code") or away_team.get("tla"),
            "kickoff_at": m.get("date") or m.get("utcDate"),
            "stage": m.get("stage"),
            "group": m.get("group"),
            "stadium": m.get("venue"),
            "status": "finished" if m.get("status") == "FINISHED" else "scheduled",
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)

    return len(matches)