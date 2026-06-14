from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    fifa_code = Column(String)
    group = Column(String)
    rating_attack = Column(Float)
    rating_defense = Column(Float)
    rating_overall = Column(Float)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    kickoff_at = Column(DateTime, nullable=False)
    stage = Column(String, nullable=False)
    group = Column(String)
    stadium = Column(String)
    status = Column(String, default="scheduled")
    result_home_goals = Column(Integer)
    result_away_goals = Column(Integer)

    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])


class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), unique=True, nullable=False)
    lambda_home = Column(Float, nullable=False)
    lambda_away = Column(Float, nullable=False)
    prob_home_win = Column(Float, nullable=False)
    prob_draw = Column(Float, nullable=False)
    prob_away_win = Column(Float, nullable=False)
    recommended_outcome = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)

    match = relationship("Match")


class Tip(Base):
    __tablename__ = "tips"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    predicted_outcome = Column(String, nullable=False)
    predicted_home_goals = Column(Integer)
    predicted_away_goals = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("match_id", "user_id", name="uix_match_user"),)

    match = relationship("Match")
    user = relationship("User")


class TipScore(Base):
    __tablename__ = "tip_scores"
    id = Column(Integer, primary_key=True, index=True)
    tip_id = Column(Integer, ForeignKey("tips.id"), unique=True, nullable=False)
    points_outcome = Column(Integer, default=0)
    points_exact = Column(Integer, default=0)
    points_bonus = Column(Integer, default=0)
    total_points = Column(Integer, default=0)

    tip = relationship("Tip")


class BookmakerTip(Base):
    __tablename__ = "bookmaker_tips"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), unique=True, nullable=False)
    odds_home = Column(Float, nullable=False)
    odds_draw = Column(Float, nullable=False)
    odds_away = Column(Float, nullable=False)
    implied_home = Column(Float, nullable=False)
    implied_draw = Column(Float, nullable=False)
    implied_away = Column(Float, nullable=False)
    recommended_outcome = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    source = Column(String, nullable=False, default="football-data")
    updated_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match")
