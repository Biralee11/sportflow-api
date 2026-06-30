from fastapi import APIRouter, Depends
from schemas.schemas import PlaceOrderRequest, UpdateOrderStatusRequest, OrderResponse
from sqlalchemy.orm import Session
from database import get_db
from services import order_service
from services.auth_service import get_current_admin, get_current_user
from typing import List

router = APIRouter(prefix="/orders", tags=["Order"])

@router.get("/", response_model=List[OrderResponse])
def get_user_orders(page: int = 1, limit: int = 20, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return order_service.get_user_orders(db, current_user.id, page, limit)

@router.get("/{id}", response_model=OrderResponse)
def get_order_by_id(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return order_service.get_order_by_id(db, id, current_user.id)

@router.post("/", response_model=OrderResponse)
def place_order(request: PlaceOrderRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return order_service.place_order(db, current_user.id, request)

@router.put("/{id}/status", response_model=OrderResponse)
def update_order_status(request: UpdateOrderStatusRequest, id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return order_service.update_order_status(db, id, request)
