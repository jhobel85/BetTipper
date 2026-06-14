from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(tags=["matches"])


@router.get("/", response_model=list[schemas.MatchWithPrediction])
def list_matches(db: Session = Depends(get_db)):
    matches = db.query(models.Match).all()
    result = []
    for m in matches:
        pred = db.query(models.ModelPrediction).filter(models.ModelPrediction.match_id == m.id).first()
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
            ),
        )
        result.append(item)
    return result
