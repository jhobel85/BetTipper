from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(tags=["tips"])


@router.get("/users/me/tips", response_model=list[schemas.TipWithScore])
def list_my_tips(db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="No user registered yet")

    tips = db.query(models.Tip).filter(models.Tip.user_id == user.id).all()
    result = []
    for tip in tips:
        score = db.query(models.TipScore).filter(models.TipScore.tip_id == tip.id).first()
        result.append(
            schemas.TipWithScore(
                match_id=tip.match_id,
                predicted_outcome=tip.predicted_outcome,
                predicted_home_goals=tip.predicted_home_goals,
                predicted_away_goals=tip.predicted_away_goals,
                points_outcome=score.points_outcome if score else 0,
                points_exact=score.points_exact if score else 0,
                points_bonus=score.points_bonus if score else 0,
                total_points=score.total_points if score else 0,
            )
        )
    return result


@router.post("/matches/{match_id}/tips", response_model=schemas.TipOut)
def create_tip(match_id: int, tip_in: schemas.TipCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="No user registered yet")

    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.kickoff_at <= datetime.utcnow() or match.status != "scheduled":
        raise HTTPException(status_code=400, detail="Tipping closed for this match")

    tip = db.query(models.Tip).filter(models.Tip.match_id == match_id, models.Tip.user_id == user.id).first()
    if not tip:
        tip = models.Tip(
            match_id=match_id,
            user_id=user.id,
            predicted_outcome=tip_in.predicted_outcome,
            predicted_home_goals=tip_in.predicted_home_goals,
            predicted_away_goals=tip_in.predicted_away_goals,
        )
        db.add(tip)
    else:
        tip.predicted_outcome = tip_in.predicted_outcome
        tip.predicted_home_goals = tip_in.predicted_home_goals
        tip.predicted_away_goals = tip_in.predicted_away_goals
    db.commit()
    db.refresh(tip)

    score = db.query(models.TipScore).filter(models.TipScore.tip_id == tip.id).first()
    total_points = score.total_points if score else 0

    return schemas.TipOut(
        match_id=match_id,
        predicted_outcome=tip.predicted_outcome,
        predicted_home_goals=tip.predicted_home_goals,
        predicted_away_goals=tip.predicted_away_goals,
        total_points=total_points,
    )
