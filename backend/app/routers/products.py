from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Category, Product, StockMovement, Supplier, User
from ..schemas import ProductIn, ProductOut, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


def _check_refs(db: Session, category_id, supplier_id):
    if category_id is not None and not db.get(Category, category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category")
    if supplier_id is not None and not db.get(Supplier, supplier_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown supplier")


def _sku_taken(db: Session, sku: str, exclude_id: int | None = None) -> bool:
    found = db.scalar(select(Product).where(Product.sku == sku))
    return found is not None and found.id != exclude_id


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = Query(None, description="search name or SKU"),
    category_id: int | None = None,
    low_stock: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Product).order_by(Product.name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if low_stock:
        stmt = stmt.where(Product.quantity <= Product.low_stock_threshold)
    return db.scalars(stmt).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductIn, db: Session = Depends(get_db), user: User = Depends(require_admin)
):
    if _sku_taken(db, data.sku):
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")
    _check_refs(db, data.category_id, data.supplier_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.flush()
    if product.quantity > 0:
        db.add(
            StockMovement(
                product_id=product.id,
                type="in",
                quantity=product.quantity,
                quantity_after=product.quantity,
                reason="Initial stock",
                user_id=user.id,
            )
        )
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    changes = data.model_dump(exclude_unset=True)
    if "sku" in changes and _sku_taken(db, changes["sku"], product_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")
    _check_refs(db, changes.get("category_id"), changes.get("supplier_id"))
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    db.delete(product)
    db.commit()
