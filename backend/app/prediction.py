import math
from typing import Tuple


def poisson_pmf(lmbda: float, k: int) -> float:
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def compute_outcome_probabilities(lambda_home: float, lambda_away: float, max_goals: int = 6):
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    for h in range(0, max_goals + 1):
        for a in range(0, max_goals + 1):
            ph = poisson_pmf(lambda_home, h)
            pa = poisson_pmf(lambda_away, a)
            p = ph * pa
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p

    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total

    probs = {"1": p_home, "X": p_draw, "2": p_away}
    sorted_outcomes = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    recommended = sorted_outcomes[0][0]
    confidence = (sorted_outcomes[0][1] - sorted_outcomes[1][1]) * 100.0

    return p_home, p_draw, p_away, recommended, confidence
