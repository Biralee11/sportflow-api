from fastapi import APIRouter, Depends
from schemas.schemas import InventoryCreateRequest, InventoryUpdateRequest, InventoryResponse
from sqlalchemy.orm import Session
from database import get_db
from services import inventory_service
from services.auth_service import get_current_admin
from typing import List

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/", response_model=List[InventoryResponse])
def get_inventory(page: int = 1, limit: int = 20, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return inventory_service.get_all_inventory(db, page, limit)

@router.get("/product/{product_id}", response_model=List[InventoryResponse])
def get_inventory_for_product(product_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return inventory_service.get_inventory_by_product(db, product_id)

@router.post("/", response_model=InventoryResponse)
def create_inventory(request: InventoryCreateRequest, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return inventory_service.create_inventory(db, request)

@router.put("/{id}", response_model=InventoryResponse)
def update_inventory(request: InventoryUpdateRequest, id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return inventory_service.update_inventory(db, id, request)

@router.delete("/{id}")
def delete_inventory(id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return inventory_service.delete_inventory(db, id)
