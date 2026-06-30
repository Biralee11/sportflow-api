from sqlalchemy.orm import Session
from models.models import UserModel
from schemas.schemas import RegisterRequest, LoginRequest, UpdateProfileRequest, ChangePasswordRequest
from fastapi import HTTPException
from services.auth_service import hash_password, verify_password, create_access_token


def register(db: Session, request: RegisterRequest):
    if db.query(UserModel).filter(UserModel.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(request.password)
    user = UserModel(email=request.email, hashed_password=hashed_password, first_name=request.first_name, last_name=request.last_name, role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, request: LoginRequest):
    user = db.query(UserModel).filter(UserModel.email == request.email).first()   
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(data={"sub": user.email, "role": user.role}), "token_type": "bearer"}

def update_profile(db: Session, user_id: int, request: UpdateProfileRequest):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if request.first_name is not None:
            user.first_name = request.first_name
    if request.last_name is not None:
            user.last_name = request.last_name
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user_id: int, request: ChangePasswordRequest):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    if verify_password(request.new_password, user.hashed_password):
         raise HTTPException(status_code=400, detail="New password must be different from current password")
    user.hashed_password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
