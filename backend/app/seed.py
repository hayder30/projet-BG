"""Initial data: first admin account + a small demo catalog (all editable in the UI)."""
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Category, Product, StockMovement, Supplier, User
from .security import hash_password


def ensure_admin(db: Session) -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    if db.scalar(select(User).where(User.username == username)):
        return
    db.add(
        User(
            username=username,
            full_name="Administrator",
            hashed_password=hash_password(password),
            role="admin",
        )
    )
    db.commit()


# Sample data only - replace with the real Brazilian Glow catalog.
DEMO_CATEGORIES = ["Skincare", "Body Care", "Hair Care", "Makeup", "Sun & Tan"]
DEMO_SUPPLIER = {"name": "Default Supplier", "phone": "", "email": ""}
DEMO_PRODUCTS = [
    # sku, name, category, price, cost, qty, threshold
    ("BG-SKN-001", "Glow Face Serum 30ml", "Skincare", 59.0, 30.0, 24, 5),
    ("BG-SKN-002", "Hydrating Day Cream 50ml", "Skincare", 45.0, 22.0, 3, 5),
    ("BG-BDY-001", "Brazilian Body Butter 200ml", "Body Care", 49.0, 24.0, 40, 8),
    ("BG-BDY-002", "Shimmer Body Oil 100ml", "Body Care", 55.0, 27.0, 0, 5),
    ("BG-HAR-001", "Nourishing Hair Mask 250ml", "Hair Care", 39.0, 18.0, 15, 5),
    ("BG-MKP-001", "Bronzing Powder", "Makeup", 35.0, 16.0, 4, 6),
    ("BG-SUN-001", "Self-Tan Drops 30ml", "Sun & Tan", 65.0, 33.0, 12, 5),
]


def seed_demo(db: Session) -> None:
    if db.scalar(select(Product).limit(1)):
        return
    cats = {}
    for name in DEMO_CATEGORIES:
        cat = Category(name=name)
        db.add(cat)
        cats[name] = cat
    supplier = Supplier(**DEMO_SUPPLIER)
    db.add(supplier)
    db.flush()
    for sku, name, cat, price, cost, qty, thr in DEMO_PRODUCTS:
        product = Product(
            sku=sku,
            name=name,
            price=price,
            cost=cost,
            quantity=qty,
            low_stock_threshold=thr,
            category_id=cats[cat].id,
            supplier_id=supplier.id,
        )
        db.add(product)
        db.flush()
        db.add(
            StockMovement(
                product_id=product.id,
                type="in",
                quantity=qty,
                quantity_after=qty,
                reason="Initial stock",
            )
        )
    db.commit()
