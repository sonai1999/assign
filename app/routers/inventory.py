
from app.services.reconciliation_worker import reconcile_inventory
from pydantic import BaseModel, Field

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product

class InventoryManifestItem(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    stock_quantity: int = Field(ge=0)


class ReconciliationRequest(BaseModel):
    items: list[InventoryManifestItem] = Field(min_length=1, max_length=1000)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("")
async def get_paginated_inventory(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_stock: int | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return active inventory with pagination and optional stock filtering."""

    query = select(Product).where(Product.is_active.is_(True))

    if min_stock is not None:
        query = query.where(Product.stock_quantity >= min_stock)

    query = query.order_by(Product.sku).limit(limit).offset(offset)

    result = await db.execute(query)
    products = result.scalars().all()

    return {
        "limit": limit,
        "offset": offset,
        "count": len(products),
        "items": [
            {
                "sku": product.sku,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "warehouse_location": product.warehouse_location,
                "base_price_usd": product.base_price_usd,
                "is_active": product.is_active,
            }
            for product in products
        ],
    }


@router.post("/reconcile", status_code=status.HTTP_202_ACCEPTED)
async def trigger_bulk_reconciliation(
    payload: ReconciliationRequest,
    background_tasks: BackgroundTasks,
):
    """Queue inventory reconciliation and immediately return 202."""

    manifest = [
        item.model_dump()
        for item in payload.items
    ]

    background_tasks.add_task(reconcile_inventory, manifest)

    return {
        "message": "Inventory reconciliation accepted",
        "status": "ACCEPTED",
        "items_submitted": len(manifest),
    }
