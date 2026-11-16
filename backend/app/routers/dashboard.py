from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Product, StockMovement, User
from ..schemas import MovementOut, ProductOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = db.scalars(select(Product).order_by(Product.quantity)).all()
    low = [p for p in products if p.is_low_stock]

    by_category: dict[str, int] = {}
    for p in products:
        key = p.category_name or "Uncategorized"
        by_category[key] = by_category.get(key, 0) + p.quantity

    recent = db.scalars(
        select(StockMovement).order_by(StockMovement.id.desc()).limit(8)
    ).all()

    return {
        "total_products": len(products),
        "total_units": sum(p.quantity for p in products),
        "stock_value_cost": round(sum(p.quantity * p.cost for p in products), 2),
        "stock_value_retail": round(sum(p.quantity * p.price for p in products), 2),
        "low_stock_count": len(low),
        "out_of_stock_count": sum(1 for p in products if p.quantity == 0),
        "low_stock_products": [ProductOut.model_validate(p).model_dump() for p in low[:10]],
        "units_by_category": by_category,
        "recent_movements": [
            MovementOut.model_validate(m).model_dump(mode="json") for m in recent
        ],
    }
