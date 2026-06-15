from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MatchBase(BaseModel):
    id: int
    home_team_name: str
    away_team_name: str
    kickoff_at: datetime
    stage: str
    group: Optional[str]
    status: str


class MatchPrediction(BaseModel):
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    recommended_outcome: str
    confidence_score: float
    reason: str


class BookmakerTipOut(BaseModel):
    recommended_outcome: str
    confidence_score: float
    odds_home: float
    odds_draw: float
    odds_away: float
    implied_home: float
    implied_draw: float
    implied_away: float
    source: str
    best_value_outcome: Optional[str] = None
    best_value_edge_pct: Optional[float] = None
    best_value_ev_pct: Optional[float] = None


class MatchWithPrediction(MatchBase):
    prediction: MatchPrediction
    bookmaker_tip: Optional[BookmakerTipOut] = None


class TipCreate(BaseModel):
    predicted_outcome: str
    predicted_home_goals: Optional[int] = None
    predicted_away_goals: Optional[int] = None


class TipOut(BaseModel):
    match_id: int
    predicted_outcome: str
    predicted_home_goals: Optional[int]
    predicted_away_goals: Optional[int]
    total_points: int


class TipWithScore(BaseModel):
    match_id: int
    predicted_outcome: str
    predicted_home_goals: Optional[int]
    predicted_away_goals: Optional[int]
    points_outcome: int
    points_exact: int
    points_bonus: int
    total_points: int

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str

    class Config:
        orm_mode = True


class MatchResult(BaseModel):
    result_home_goals: int
    result_away_goals: int


class GroupQualificationProbability(BaseModel):
    group: str
    team: str
    fifa_code: str
    qualify_probability: float
    first_place_probability: float
    position_probabilities: dict[str, float]


class TournamentProbability(BaseModel):
    team: str
    fifa_code: str
    round_of_32_probability: float
    round_of_16_probability: float
    quarterfinal_probability: float
    semifinal_probability: float
    final_probability: float
    champion_probability: float


class TournamentSimulationOut(BaseModel):
    simulations: int
    group_qualification_probabilities: dict[str, list[GroupQualificationProbability]]
    tournament_probabilities: list[TournamentProbability]
