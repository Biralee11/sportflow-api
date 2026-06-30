from database import Base
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Numeric, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,autoincrement=True)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True,autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    category = Column(String, nullable=False)
    image_url = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class InventoryModel(Base):
    __tablename__ = "inventory"
    id = Column(Integer,primary_key=True,autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    items = relationship("OrderItemModel", back_populates="order")
    payment = relationship("PaymentModel", uselist=False, back_populates="order")

class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer,primary_key=True,autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False) 
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Numeric(precision=10, scale=2), nullable=False)
    order = relationship("OrderModel", back_populates="items")

class PaymentModel(Base):
    __tablename__ = "payments"
    id = Column(Integer,primary_key=True,autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    order = relationship("OrderModel", back_populates="payment")