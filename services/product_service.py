from sqlalchemy.orm import Session
from models.models import ProductModel
from schemas.schemas import ProductCreateRequest, ProductUpdateRequest
from fastapi import HTTPException

def get_all_products(db: Session, page: int, limit: int):
    all_products = db.query(ProductModel).filter(ProductModel.is_active == True).offset((page - 1) * limit).limit(limit).all()
    return all_products

def get_product_by_id(db: Session, id: int):
    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def create_product(db: Session, request: ProductCreateRequest):
    product = ProductModel(name=request.name, description=request.description, price=request.price, category=request.category, image_url=request.image_url)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def update_product(db: Session, id: int, request: ProductUpdateRequest):
    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if request.name is not None:
            product.name = request.name
    if request.description is not None:
            product.description = request.description
    if request.price is not None:
            product.price = request.price
    if request.category is not None:
            product.category = request.category
    if request.image_url is not None:
            product.image_url = request.image_url
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, id: int):
    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
      raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    db.refresh(product)
    return product