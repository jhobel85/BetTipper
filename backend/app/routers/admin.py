from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(tags=["admin"])


@router.post("/admin/matches/{match_id}/result")
def enter_match_result(match_id: int, result_in: schemas.MatchResult, db: Session = Depends(get_db)):
    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.result_home_goals = result_in.result_home_goals
    match.result_away_goals = result_in.result_away_goals
    match.status = "finished"
    db.commit()

    prediction = db.query(models.ModelPrediction).filter(models.ModelPrediction.match_id == match_id).first()
    tips = db.query(models.Tip).filter(models.Tip.match_id == match_id).all()

    if result_in.result_home_goals > result_in.result_away_goals:
        actual_outcome = "1"
    elif result_in.result_home_goals == result_in.result_away_goals:
        actual_outcome = "X"
    else:
        actual_outcome = "2"

    for tip in tips:
        exact_match = (
            tip.predicted_home_goals is not None
            and tip.predicted_away_goals is not None
            and tip.predicted_home_goals == result_in.result_home_goals
            and tip.predicted_away_goals == result_in.result_away_goals
        )
        outcome_correct = tip.predicted_outcome == actual_outcome
        points_outcome = 3 if outcome_correct and not exact_match else 0
        points_exact = 5 if exact_match else 0
        points_bonus = 1 if outcome_correct and prediction and prediction.confidence_score < 33 else 0
        total_points = points_exact if exact_match else (points_outcome + points_bonus)

        tip_score = db.query(models.TipScore).filter(models.TipScore.tip_id == tip.id).first()
        if not tip_score:
            tip_score = models.TipScore(tip_id=tip.id)
            db.add(tip_score)

        tip_score.points_outcome = points_outcome
        tip_score.points_exact = points_exact
        tip_score.points_bonus = points_bonus
        tip_score.total_points = total_points

    db.commit()
    return {"status": "ok", "tips_scored": len(tips)}
