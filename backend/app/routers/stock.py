from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Product, StockMovement, User
from ..schemas import MovementIn, MovementOut

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.post("/movements", response_model=MovementOut, status_code=201)
def create_movement(
    data: MovementIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """in = add units, out = remove units, adjust = set the stock to an exact count."""
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    if data.type == "in":
        product.quantity += data.quantity
    elif data.type == "out":
        if data.quantity > product.quantity:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock (available: {product.quantity})",
            )
        product.quantity -= data.quantity
    else:  # adjust
        product.quantity = data.quantity

    movement = StockMovement(
        product_id=product.id,
        type=data.type,
        quantity=data.quantity,
        quantity_after=product.quantity,
        reason=data.reason,
        user_id=user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    product_id: int | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(StockMovement).order_by(StockMovement.id.desc()).limit(limit)
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    return db.scalars(stmt).all()
