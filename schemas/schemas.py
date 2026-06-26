from pydantic import BaseModel, field_validator, EmailStr, Field
import re
from datetime import datetime
from typing import Optional
from decimal import Decimal

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)

        
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[^a-zA-Z0-9]", value):
            raise ValueError("Password must contain at least one special character")
        return value

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    price: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    category: str
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class InventoryCreateRequest(BaseModel):
    product_id: int = Field(gt=0)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=0)

class InventoryUpdateRequest(BaseModel):
    size: Optional[str] = Field(None, max_length=20)
    quantity: Optional[int] = Field(None, ge=0)

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    size: str
    quantity: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class CartItemRequest(BaseModel):
    product_id: int = Field(gt=0)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(gt=0)

class CartItemResponse(BaseModel):
    product_id: int
    size: str
    quantity: int
    price: Decimal