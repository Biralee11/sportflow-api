from sqlalchemy.orm import Session
from models.models import OrderModel, OrderItemModel, ProductModel, InventoryModel
from schemas.schemas import PlaceOrderRequest, UpdateOrderStatusRequest
from fastapi import HTTPException
from services import cart_service, inventory_service, payment_service
from decimal import Decimal

def place_order(db:Session, user_id: int, request: PlaceOrderRequest):
    cart_items = cart_service.get_cart(user_id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    total_amount = Decimal("0")
    order_items_data = []
    for item in cart_items:
        product = db.query(ProductModel).filter(ProductModel.id == item["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.is_active is False:
            raise HTTPException(status_code=400, detail=f"Product {product.name} is no longer available")
        current_price = product.price
        total_amount += current_price * item["quantity"]
        inventory = db.query(InventoryModel).filter(
            InventoryModel.product_id == item["product_id"],
            InventoryModel.size == item["size"]
        ).first()
        if not inventory:
            raise HTTPException(status_code=400, detail=f"Size {item['size']} not available for this product")
        inventory_service.decrement_stock(db, inventory.id, item["quantity"])
        order_items_data.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": current_price,
            "size": item["size"]
        })

    # now create the order
    order = OrderModel(user_id=user_id, total_amount=total_amount, status="pending")
    db.add(order)
    db.flush()  # assigns order.id without committing

    # now create order_items using order.id
    for item_data in order_items_data:
        order_item = OrderItemModel(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price"]
        )
        db.add(order_item)
    payment_service.create_payment(db, order.id, total_amount, request.payment_method)
    cart_service.clear_cart(user_id)
    db.commit()
    db.refresh(order)
    return order

def get_user_orders(db:Session, user_id: int, page: int, limit: int):
    all_orders = db.query(OrderModel).filter(OrderModel.user_id == user_id).offset((page - 1) * limit).limit(limit).all()
    return all_orders

def get_order_by_id(db:Session, id: int, user_id: int):
    order = db.query(OrderModel).filter(OrderModel.id == id, OrderModel.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

def update_order_status(db:Session, id: int, request: UpdateOrderStatusRequest):
    order = db.query(OrderModel).filter(OrderModel.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = request.status
    db.commit()
    db.refresh(order)
    return order
