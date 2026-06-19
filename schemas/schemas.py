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
    name: str
    description: str
    price: Decimal
    category: str
    image_url: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

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
    product_id: int
    size: str
    quantity: int

class InventoryUpdateRequest(BaseModel):
    size: Optional[str] = None
    quantity: Optional[int] = None

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    size: str
    quantity: int
    created_at: datetime
    updated_at: Optional[datetime] = None