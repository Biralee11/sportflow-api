from sqlalchemy.orm import Session
from models.models import OrderModel, OrderItemModel, ProductModel, InventoryModel
from schemas.schemas import PlaceOrderRequest, UpdateOrderStatusRequest
from fastapi import HTTPException
from services import cart_service, inventory_service, payment_service
from decimal import Decimal

def place_order(db:Session, user_id: int, request: PlaceOrderRequest):
    # Checkout is one atomic transaction: order, order_items, payment, stock decrement
    # and cart clear either all succeed together or all roll back. There is a single
    # commit at the very end, so any failure before it leaves the database untouched.
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
        # Price is always taken from the database at checkout, never trusted from the
        # cart or client, so a stale or tampered price can never be charged.
        current_price = product.price
        total_amount += current_price * item["quantity"]
        inventory = db.query(InventoryModel).filter(
            InventoryModel.product_id == item["product_id"],
            InventoryModel.size == item["size"]
        ).first()
        if not inventory:
            raise HTTPException(status_code=400, detail=f"Size {item['size']} not available for this product")
        # Locks the row and reduces stock; raises 409 if another checkout got there first.
        inventory_service.decrement_stock(db, inventory.id, item["quantity"])
        order_items_data.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": current_price,
            "size": item["size"]
        })

    order = OrderModel(user_id=user_id, total_amount=total_amount, status="pending")
    db.add(order)
    db.flush()  # assigns order.id within the transaction so order_items can reference it, without committing yet

    for item_data in order_items_data:
        order_item = OrderItemModel(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price"]  # snapshot of price, immune to later product price changes
        )
        db.add(order_item)
    # Payment shares this same transaction (no commit inside create_payment) so it
    # rolls back with everything else if anything fails.
    payment_service.create_payment(db, order.id, total_amount, request.payment_method)
    cart_service.clear_cart(user_id)
    db.commit()
    db.refresh(order)
    return order

def get_user_orders(db:Session, user_id: int, page: int, limit: int):
    all_orders = db.query(OrderModel).filter(OrderModel.user_id == user_id).offset((page - 1) * limit).limit(limit).all()
    return all_orders

def get_order_by_id(db:Session, id: int, user_id: int):
    # Filters on user_id as well as id (IDOR protection): a customer can only ever
    # retrieve their own order, never someone else's by guessing an id.
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
