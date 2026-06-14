from fastapi import FastAPI
from .db import Base, engine, SessionLocal
from .sample_data import init_sample_data
from .routers import admin, auth, matches, tips, leaderboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MS 2026 Tipper")

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(matches.router, prefix="/api/v1/matches")
app.include_router(tips.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

with SessionLocal() as db:
    init_sample_data(db)
