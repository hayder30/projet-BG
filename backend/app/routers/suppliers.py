from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Supplier, User
from ..schemas import SupplierIn, SupplierOut

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(data: SupplierIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.scalar(select(Supplier).where(Supplier.name == data.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Supplier already exists")
    sup = Supplier(**data.model_dump())
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return sup


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    sup = db.get(Supplier, supplier_id)
    if not sup:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    if sup.products:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Supplier still has products")
    db.delete(sup)
    db.commit()
