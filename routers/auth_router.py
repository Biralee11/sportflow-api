from fastapi import APIRouter, Depends
from schemas.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from sqlalchemy.orm import Session
from database import get_db
from services import user_service
from fastapi import Request
from limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
@limiter.limit("10/hour")
def register(request: Request, credentials: RegisterRequest, db: Session = Depends(get_db)):
    return user_service.register(db, credentials)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    return user_service.login(db, credentials)
