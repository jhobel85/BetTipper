from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Team, Match, ModelPrediction
from .prediction import compute_outcome_probabilities


def init_sample_data(db: Session):
    if db.query(Team).count() > 0:
        return

    teams = [
        Team(name="Brazil", fifa_code="BRA", group="A", rating_attack=1.5, rating_defense=0.5, rating_overall=2.0),
        Team(name="Germany", fifa_code="GER", group="A", rating_attack=1.4, rating_defense=0.6, rating_overall=2.0),
        Team(name="France", fifa_code="FRA", group="B", rating_attack=1.6, rating_defense=0.5, rating_overall=2.1),
        Team(name="Argentina", fifa_code="ARG", group="B", rating_attack=1.5, rating_defense=0.6, rating_overall=2.1),
    ]
    db.add_all(teams)
    db.commit()

    teams = db.query(Team).all()
    now = datetime.utcnow()

    matches = [
        Match(
            home_team_id=teams[0].id,
            away_team_id=teams[1].id,
            kickoff_at=now + timedelta(days=1),
            stage="Group",
            group="A",
            stadium="Stadium 1",
            status="scheduled",
        ),
        Match(
            home_team_id=teams[2].id,
            away_team_id=teams[3].id,
            kickoff_at=now + timedelta(days=2),
            stage="Group",
            group="B",
            stadium="Stadium 2",
            status="scheduled",
        ),
    ]
    db.add_all(matches)
    db.commit()

    matches = db.query(Match).all()
    for m in matches:
        home = db.query(Team).get(m.home_team_id)
        away = db.query(Team).get(m.away_team_id)
        lambda_home = 1.2 + (home.rating_attack - away.rating_defense) * 0.3
        lambda_away = 1.0 + (away.rating_attack - home.rating_defense) * 0.3
        p1, px, p2, rec, conf = compute_outcome_probabilities(lambda_home, lambda_away)
        pred = ModelPrediction(
            match_id=m.id,
            lambda_home=lambda_home,
            lambda_away=lambda_away,
            prob_home_win=p1,
            prob_draw=px,
            prob_away_win=p2,
            recommended_outcome=rec,
            confidence_score=conf,
        )
        db.add(pred)
    db.commit()
