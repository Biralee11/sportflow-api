from fastapi import APIRouter, Depends, HTTPException
from schemas.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from sqlalchemy.orm import Session
from database import get_db
from models.models import UserModel
from services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(request.password)
    user = UserModel(email=request.email, hashed_password=hashed_password, first_name=request.first_name, last_name=request.last_name, role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == request.email).first()   
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(data={"sub": user.email, "role": user.role}), "token_type": "bearer"}