from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
import hashlib

router = APIRouter(tags=["auth"])


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    u = models.User(
        email=user.email,
        password_hash=hash_password(user.password),
        display_name=user.display_name,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/login", response_model=schemas.UserOut)
def login(login_request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_request.email).first()
    if not user or user.password_hash != hash_password(login_request.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    return user
