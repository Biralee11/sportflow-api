from fastapi import APIRouter, Depends
from schemas.schemas import ProductCreateRequest, ProductResponse, ProductUpdateRequest
from sqlalchemy.orm import Session
from database import get_db
from services import product_service
from services.auth_service import get_current_admin
from typing import List

router = APIRouter(prefix="/products", tags=["Product"])

@router.get("/", response_model=List[ProductResponse])
def get_products(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    return product_service.get_all_products(db, page, limit)

@router.get("/{id}", response_model=ProductResponse)
def get_product(id: int, db: Session = Depends(get_db)):
    return product_service.get_product_by_id(db, id)

@router.post("/", response_model=ProductResponse)
def create_product(request: ProductCreateRequest, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return product_service.create_product(db, request)

@router.put("/{id}", response_model=ProductResponse)
def update_product(request: ProductUpdateRequest, id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return product_service.update_product(db, id, request)

@router.delete("/{id}", response_model=ProductResponse)
def delete_product(id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return product_service.delete_product(db, id)

@router.post("/{id}/reactivate", response_model=ProductResponse)
def reactivate_product(id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return product_service.reactivate_product(db, id)