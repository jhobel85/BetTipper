from typing import Any


def merge_all(
    match_data: list[dict[str, Any]],
    fbref: dict[int, dict[str, float]],
    understat: dict[int, dict[str, float]],
    odds: dict[int, dict[str, float]],
    injuries: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []

    for m in match_data:
        match_id = int(m.get("id"))
        home_team = m.get("homeTeam") or {}
        away_team = m.get("awayTeam") or {}

        merged.append(
            {
                "match_id": match_id,
                "home_name": home_team.get("name"),
                "home_code": home_team.get("code") or home_team.get("tla"),
                "away_name": away_team.get("name"),
                "away_code": away_team.get("code") or away_team.get("tla"),
                "kickoff_at": m.get("utcDate"),
                "stage": m.get("stage"),
                "group": m.get("group"),
                "status": m.get("status"),
                "score": m.get("score"),
                "xg_home": (fbref.get(match_id) or {}).get("xG_home")
                or (understat.get(match_id) or {}).get("xG_home"),
                "xg_away": (fbref.get(match_id) or {}).get("xG_away")
                or (understat.get(match_id) or {}).get("xG_away"),
                "odds": odds.get(match_id),
                "injuries": injuries.get(match_id),
            }
        )

    return merged
