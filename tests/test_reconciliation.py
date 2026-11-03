
import pytest
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models import Product, ReconciliationAuditLog
from app.services.reconciliation_worker import reconcile_inventory


@pytest.mark.asyncio
async def test_reconciliation_updates_stock_and_writes_audit():
    test_sku = "TEST-RECON-001"
    audit_id = None

    # Create a dedicated test product.
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                delete(Product).where(Product.sku == test_sku)
            )

            product = Product(
                sku=test_sku,
                name="Reconciliation Test Product",
                stock_quantity=10,
                warehouse_location="TEST-WH",
                base_price_usd=9.99,
                is_active=True,
            )
            session.add(product)

    try:
        # Run the actual background worker.
        await reconcile_inventory(
            [
                {
                    "sku": test_sku,
                    "stock_quantity": 25,
                }
            ]
        )

        # Verify the stock update and audit record.
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Product).where(Product.sku == test_sku)
            )
            updated_product = result.scalar_one()

            assert updated_product.stock_quantity == 25

            result = await session.execute(
                select(ReconciliationAuditLog)
                .order_by(ReconciliationAuditLog.id.desc())
                .limit(1)
            )
            audit = result.scalar_one()

            audit_id = audit.id

            assert audit.status == "SUCCESS"
            assert audit.skus_processed == 1
            assert audit.error_message is None

    finally:
        # Remove test data without deleting existing inventory.
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await session.execute(
                    delete(Product).where(Product.sku == test_sku)
                )

                if audit_id is not None:
                    await session.execute(
                        delete(ReconciliationAuditLog).where(
                            ReconciliationAuditLog.id == audit_id
                        )
                    )
