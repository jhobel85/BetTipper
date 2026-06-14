from typing import Any


def get_odds(match_data: list[dict[str, Any]] | None = None) -> dict[int, dict[str, float]]:
    """
    Extract odds from football-data payload when present.
    Returns {match_id: {"home": float, "draw": float, "away": float}}
    """
    if not match_data:
        return {}

    out: dict[int, dict[str, float]] = {}
    for m in match_data:
        match_id = m.get("id")
        odds = m.get("odds") or {}
        if not match_id or not odds:
            continue
        home = odds.get("homeWin")
        draw = odds.get("draw")
        away = odds.get("awayWin")
        if home is None or draw is None or away is None:
            continue
        try:
            out[int(match_id)] = {"home": float(home), "draw": float(draw), "away": float(away)}
        except Exception:
            continue
    return out
