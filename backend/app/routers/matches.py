from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(tags=["matches"])


def _value_opportunity(
    prob_home: float,
    prob_draw: float,
    prob_away: float,
    odds_home: float,
    odds_draw: float,
    odds_away: float,
) -> tuple[str | None, float | None, float | None]:
    candidates = {
        "1": (prob_home, odds_home),
        "X": (prob_draw, odds_draw),
        "2": (prob_away, odds_away),
    }
    best_outcome: str | None = None
    best_edge_pct: float | None = None
    best_ev_pct: float | None = None
    for outcome, (model_prob, odds) in candidates.items():
        implied_prob = 1.0 / odds if odds > 0 else 0.0
        edge = model_prob - implied_prob
        ev = (model_prob * odds) - 1.0
        if best_ev_pct is None or ev > best_ev_pct:
            best_outcome = outcome
            best_edge_pct = edge * 100.0
            best_ev_pct = ev * 100.0
    if best_ev_pct is None or best_ev_pct <= 0:
        return None, None, None
    return best_outcome, best_edge_pct, best_ev_pct


def _prediction_reason(
    home_name: str,
    away_name: str,
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    lambda_home: float,
    lambda_away: float,
    prob_home: float,
    prob_draw: float,
    prob_away: float,
    recommended: str,
    confidence: float,
) -> str:
    p1 = prob_home * 100
    px = prob_draw * 100
    p2 = prob_away * 100
    core = (
        f"Data signal: {home_name} attack {home_attack:.2f} vs {away_name} defense {away_defense:.2f}, "
        f"and {away_name} attack {away_attack:.2f} vs {home_name} defense {home_defense:.2f}. "
        f"Expected goals λ: {home_name} {lambda_home:.2f}, {away_name} {lambda_away:.2f}. "
    )
    if confidence < 1.0:
        return (
            core
            + f"Outcome probabilities are nearly tied (1={p1:.1f}%, X={px:.1f}%, 2={p2:.1f}%), "
            "so confidence is very low."
        )
    if recommended == "1":
        return (
            core
            + f"{home_name} has the highest model win probability ({p1:.1f}%) "
            f"vs draw ({px:.1f}%) and {away_name} win ({p2:.1f}%)."
        )
    if recommended == "2":
        return (
            core
            + f"{away_name} has the highest model win probability ({p2:.1f}%) "
            f"vs draw ({px:.1f}%) and {home_name} win ({p1:.1f}%)."
        )
    return (
        core
        + f"Draw is the top model outcome ({px:.1f}%) with alternatives: "
        f"{home_name} win {p1:.1f}% and {away_name} win {p2:.1f}%."
    )


@router.get("/", response_model=list[schemas.MatchWithPrediction])
def list_matches(db: Session = Depends(get_db)):
    matches = db.query(models.Match).all()
    result = []
    for m in matches:
        pred = db.query(models.ModelPrediction).filter(models.ModelPrediction.match_id == m.id).first()
        if not pred:
            continue
        bookmaker = db.query(models.BookmakerTip).filter(models.BookmakerTip.match_id == m.id).first()
        best_value_outcome: str | None = None
        best_value_edge_pct: float | None = None
        best_value_ev_pct: float | None = None
        if bookmaker:
            (
                best_value_outcome,
                best_value_edge_pct,
                best_value_ev_pct,
            ) = _value_opportunity(
                prob_home=pred.prob_home_win,
                prob_draw=pred.prob_draw,
                prob_away=pred.prob_away_win,
                odds_home=bookmaker.odds_home,
                odds_draw=bookmaker.odds_draw,
                odds_away=bookmaker.odds_away,
            )
        reason = _prediction_reason(
            home_name=m.home_team.name,
            away_name=m.away_team.name,
            home_attack=float(m.home_team.rating_attack or 1.0),
            home_defense=float(m.home_team.rating_defense or 1.0),
            away_attack=float(m.away_team.rating_attack or 1.0),
            away_defense=float(m.away_team.rating_defense or 1.0),
            lambda_home=float(pred.lambda_home),
            lambda_away=float(pred.lambda_away),
            prob_home=pred.prob_home_win,
            prob_draw=pred.prob_draw,
            prob_away=pred.prob_away_win,
            recommended=pred.recommended_outcome,
            confidence=pred.confidence_score,
        )
        item = schemas.MatchWithPrediction(
            id=m.id,
            home_team_name=m.home_team.name,
            away_team_name=m.away_team.name,
            kickoff_at=m.kickoff_at,
            stage=m.stage,
            group=m.group,
            status=m.status,
            prediction=schemas.MatchPrediction(
                prob_home_win=pred.prob_home_win,
                prob_draw=pred.prob_draw,
                prob_away_win=pred.prob_away_win,
                recommended_outcome=pred.recommended_outcome,
                confidence_score=pred.confidence_score,
                reason=reason,
            ),
            bookmaker_tip=(
                schemas.BookmakerTipOut(
                    recommended_outcome=bookmaker.recommended_outcome,
                    confidence_score=bookmaker.confidence_score,
                    odds_home=bookmaker.odds_home,
                    odds_draw=bookmaker.odds_draw,
                    odds_away=bookmaker.odds_away,
                    implied_home=bookmaker.implied_home,
                    implied_draw=bookmaker.implied_draw,
                    implied_away=bookmaker.implied_away,
                    source=bookmaker.source,
                    best_value_outcome=best_value_outcome,
                    best_value_edge_pct=best_value_edge_pct,
                    best_value_ev_pct=best_value_ev_pct,
                )
                if bookmaker
                else None
            ),
        )
        result.append(item)
    return result
