import os

from fastapi import FastAPI
from .data_loader import load_matches_from_json, load_teams_from_json, recompute_predictions, reset_real_data_state
from .db import Base, engine, SessionLocal
from .match_generator import DEFAULT_FIFA_RAW_PATH, DEFAULT_OUTPUT_PATH, generate_matches_from_fifa_api
from .sample_data import init_sample_data
from .routers import admin, auth, matches, tips, leaderboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MS 2026 Tipper")

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(matches.router, prefix="/api/v1/matches")
app.include_router(tips.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


def _is_truthy_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


with SessionLocal() as db:
    if _is_truthy_env("BT_AUTO_LOAD_REAL_DATA"):
        if _is_truthy_env("BT_REPLACE_EXISTING_DATA", default=True):
            reset_real_data_state(db)
        load_teams_from_json(db)
        if DEFAULT_FIFA_RAW_PATH.exists():
            generate_matches_from_fifa_api(DEFAULT_FIFA_RAW_PATH, DEFAULT_OUTPUT_PATH)
        load_matches_from_json(db)
        recompute_predictions(db)

if _is_truthy_env("BT_ENABLE_SAMPLE_SEED"):
    with SessionLocal() as db:
        init_sample_data(db)
