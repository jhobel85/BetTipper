from typing import Any


def get_understat(match_data: list[dict[str, Any]] | None = None) -> dict[int, dict[str, float]]:
    """
    Optional Understat integration.
    Returns mapping keyed by match_id with xG-like enrichments when available.
    """
    if not match_data:
        return {}

    try:
        from understatapi import UnderstatClient  # type: ignore
    except Exception:
        return {}

    # No direct WC match-id mapping guaranteed here.
    # Keep integration non-breaking and return empty until reliable mapping is added.
    try:
        _ = UnderstatClient()
    except Exception:
        return {}

    return {}
