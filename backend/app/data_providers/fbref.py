from typing import Any


def get_fbref_stats(match_data: list[dict[str, Any]] | None = None) -> dict[int, dict[str, float]]:
    """
    Optional FBref integration.
    Returns mapping: {match_id: {"xG_home": float, "xG_away": float}}
    Falls back to empty map when dependency/data is unavailable.
    """
    if not match_data:
        return {}

    try:
        # Optional dependency; not required for app runtime.
        from soccerdata import FBref  # type: ignore
    except Exception:
        return {}

    try:
        fb = FBref(leagues="FIFA World Cup", seasons=2026)
        results = fb.read_match_results()
    except Exception:
        return {}

    if results is None or len(results) == 0:
        return {}

    # Best-effort mapping by home/away names + date where possible.
    match_map: dict[tuple[str, str, str], int] = {}
    for m in match_data:
        home = (m.get("homeTeam") or {}).get("name", "")
        away = (m.get("awayTeam") or {}).get("name", "")
        date = str(m.get("utcDate", ""))[:10]
        if home and away and date:
            match_map[(home.lower(), away.lower(), date)] = int(m.get("id"))

    out: dict[int, dict[str, float]] = {}
    for _, row in results.iterrows():
        home = str(row.get("home_team", "")).lower()
        away = str(row.get("away_team", "")).lower()
        date = str(row.get("date", ""))[:10]
        key = (home, away, date)
        match_id = match_map.get(key)
        if not match_id:
            continue
        xg_home = row.get("home_xg")
        xg_away = row.get("away_xg")
        if xg_home is None or xg_away is None:
            continue
        try:
            out[match_id] = {"xG_home": float(xg_home), "xG_away": float(xg_away)}
        except Exception:
            continue

    return out
