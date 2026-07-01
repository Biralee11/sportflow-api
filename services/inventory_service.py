from sqlalchemy.orm import Session
from models.models import InventoryModel
from schemas.schemas import InventoryCreateRequest, InventoryUpdateRequest
from fastapi import HTTPException

def get_all_inventory(db: Session, page: int, limit: int):
    all_inventory = db.query(InventoryModel).offset((page - 1) * limit).limit(limit).all()
    return all_inventory

def get_inventory_by_product(db: Session, product_id: int):
    # Returns a list: a single product can have many size variants, each its own row.
    inventory = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).all()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory

def create_inventory(db: Session, request: InventoryCreateRequest):
    inventory = InventoryModel(product_id=request.product_id, size=request.size, quantity=request.quantity)
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory

def update_inventory(db: Session, id: int, request: InventoryUpdateRequest):
    inventory = db.query(InventoryModel).filter(InventoryModel.id == id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    if request.size is not None:
            inventory.size = request.size
    if request.quantity is not None:
            inventory.quantity = request.quantity
    db.commit()
    db.refresh(inventory)
    return inventory

def delete_inventory(db: Session, id: int):
    # Hard delete is safe here: order_items captures product and price at purchase time,
    # so removing a size variant never orphans historical order data.
    inventory = db.query(InventoryModel).filter(InventoryModel.id == id).first()
    if not inventory:
      raise HTTPException(status_code=404, detail="Inventory not found")
    db.delete(inventory)
    db.commit()
    return {"message": "Inventory deleted successfully"}

def decrement_stock(db: Session, id: int, quantity_requested: int):
    # with_for_update() locks this inventory row for the duration of the transaction.
    # Concurrent checkouts for the same item must wait for this lock, so two customers
    # cannot both buy the last unit - the second sees the updated quantity and is rejected.
    # The lock is released automatically on commit.
    inventory = db.query(InventoryModel).filter(InventoryModel.id == id).with_for_update().first()
    if not inventory:
      raise HTTPException(status_code=404, detail="Inventory not found")
    if quantity_requested > inventory.quantity:
         raise HTTPException(status_code=409, detail="Insufficient stock available")
    inventory.quantity -= quantity_requested
    db.commit()
    db.refresh(inventory)
    return inventory
