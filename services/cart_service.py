import redis
from config import REDIS_URL
from schemas.schemas import CartItemRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models import ProductModel
import json

redis_client = redis.from_url(REDIS_URL)

def add_to_cart(db: Session, user_id: int, request: CartItemRequest):
        product = db.query(ProductModel).filter(ProductModel.id == request.product_id).first()
        if not product or product.is_active is False:
            raise HTTPException(status_code=404, detail="Product not found")
        cart_key = f"cart:{user_id}"
        item_key = f"{request.product_id}:{request.size}"
        item_data = json.dumps({
            "product_id": request.product_id,
            "size": request.size,
            "quantity": request.quantity,
            "price": str(product.price)
        })
        redis_client.hset(cart_key, item_key, item_data)

def get_cart(user_id: int):
        cart_key = f"cart:{user_id}"
        cart = redis_client.hgetall(cart_key)
        return [json.loads(item) for item in cart.values()]

def remove_from_cart(user_id: int, product_id: int, size: str):
        cart_key = f"cart:{user_id}"
        item_key = f"{product_id}:{size}"
        redis_client.hdel(cart_key, item_key)

def clear_cart(user_id: int):
    cart_key = f"cart:{user_id}"
    redis_client.delete(cart_key)