from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    full_name: str = ""
    role: Literal["admin", "staff"] = "staff"


class UserOut(ORM):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- categories / suppliers ----------
class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class CategoryOut(ORM):
    id: int
    name: str


class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = ""
    email: str = ""


class SupplierOut(ORM):
    id: int
    name: str
    phone: str
    email: str


# ---------- products ----------
class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    price: float = Field(ge=0)
    cost: float = Field(default=0, ge=0)
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    category_id: int | None = None
    supplier_id: int | None = None


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)
    category_id: int | None = None
    supplier_id: int | None = None


class ProductOut(ORM):
    id: int
    sku: str
    name: str
    description: str
    price: float
    cost: float
    quantity: int
    low_stock_threshold: int
    category_id: int | None
    category_name: str | None
    supplier_id: int | None
    supplier_name: str | None
    is_low_stock: bool


# ---------- stock ----------
class MovementIn(BaseModel):
    product_id: int
    type: Literal["in", "out", "adjust"]
    quantity: int = Field(ge=0)
    reason: str = Field(default="", max_length=200)


class MovementOut(ORM):
    id: int
    product_id: int
    product_name: str
    type: str
    quantity: int
    quantity_after: int
    reason: str
    username: str | None
    created_at: datetime
