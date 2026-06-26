from fastapi import APIRouter, Depends
from schemas.schemas import CartItemRequest, CartItemResponse
from sqlalchemy.orm import Session
from database import get_db
from services import cart_service
from services.auth_service import get_current_user
from typing import List


router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("/")
def add_to_cart(request: CartItemRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return cart_service.add_to_cart(db, current_user.id, request)

@router.get("/", response_model=List[CartItemResponse])
def get_cart(current_user = Depends(get_current_user)):
    return cart_service.get_cart(current_user.id)

@router.delete("/{product_id}/{size}")
def delete_from_cart(product_id: int, size: str, current_user = Depends(get_current_user)):
    return cart_service.remove_from_cart(current_user.id, product_id, size)