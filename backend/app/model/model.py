import math
from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class MatchFeatures:
    rating_home: float
    rating_away: float
    xg_home: float
    xg_away: float
    home_advantage: float
    odds_home: float | None = None
    odds_draw: float | None = None
    odds_away: float | None = None


@dataclass
class ModelParams:
    intercept_home: float
    intercept_away: float
    beta_rating: float
    beta_xg: float
    beta_home_adv: float


def poisson_p(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def outcome_probs(lambda_home: float, lambda_away: float, max_goals: int = 8) -> Tuple[float, float, float]:
    p_home = p_draw = p_away = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_p(h, lambda_home) * poisson_p(a, lambda_away)
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p
    total = p_home + p_draw + p_away
    if total > 0:
        return p_home / total, p_draw / total, p_away / total
    return 0.0, 0.0, 0.0


def predict_match(features: MatchFeatures, params: ModelParams) -> dict:
    lambda_home = math.exp(
        params.intercept_home
        + params.beta_rating * (features.rating_home - features.rating_away)
        + params.beta_xg * (features.xg_home - features.xg_away)
        + params.beta_home_adv * features.home_advantage
    )

    lambda_away = math.exp(
        params.intercept_away
        + params.beta_rating * (features.rating_away - features.rating_home)
        + params.beta_xg * (features.xg_away - features.xg_home)
    )

    p1, px, p2 = outcome_probs(lambda_home, lambda_away)

    probs = {"1": p1, "X": px, "2": p2}
    sorted_outcomes = sorted(probs.items(), key=lambda item: item[1], reverse=True)
    top_outcome, top_prob = sorted_outcomes[0]
    second_prob = sorted_outcomes[1][1] if len(sorted_outcomes) > 1 else 0.0
    conf = (top_prob - second_prob) * 100

    # Do not force a directional tip when model separation is negligible.
    rec = "X" if conf < 1.0 else top_outcome

    return {
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "prob_home_win": p1,
        "prob_draw": px,
        "prob_away_win": p2,
        "recommended_outcome": rec,
        "confidence_score": conf
    }
