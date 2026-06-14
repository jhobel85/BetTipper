from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/global")
def global_leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(models.User.display_name, models.TipScore.total_points)
        .join(models.Tip, models.Tip.id == models.TipScore.tip_id)
        .join(models.User, models.User.id == models.Tip.user_id)
        .all()
    )
    agg = {}
    for name, pts in rows:
        agg[name] = agg.get(name, 0) + pts
    return [{"display_name": k, "total_points": v} for k, v in sorted(agg.items(), key=lambda x: x[1], reverse=True)]
