from fastapi import APIRouter, Depends
from schemas.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from sqlalchemy.orm import Session
from database import get_db
from services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return user_service.register(db, request)

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return user_service.login(db, request)