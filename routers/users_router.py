from fastapi import APIRouter, Depends
from schemas.schemas import UserResponse, UpdateProfileRequest, ChangePasswordRequest
from sqlalchemy.orm import Session
from database import get_db
from services import user_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(request: UpdateProfileRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return user_service.update_profile(db, current_user.id, request)

@router.put("/me/password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return user_service.change_password(db, current_user.id, request)