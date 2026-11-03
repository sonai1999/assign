
import asyncio
import logging
import random
import sqlite3
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.database import AsyncSessionLocal
from app.models import Product, ReconciliationAuditLog

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def reconcile_inventory(manifest: list[dict]) -> None:
    """
    Reconcile inventory in a background task.

    Each attempt uses its own database session and transaction.
    SQLite locking errors are retried up to three times.
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    skus_processed = 0

                    for item in manifest:
                        result = await session.execute(
                            select(Product).where(
                                Product.sku == item["sku"]
                            )
                        )
                        product = result.scalar_one_or_none()

                        if product is None:
                            logger.warning(
                                "Reconciliation SKU not found: %s",
                                item["sku"],
                            )
                            continue

                        product.stock_quantity = item["stock_quantity"]
                        skus_processed += 1

                # The transaction has committed successfully here.

            await _write_audit(
                status="SUCCESS",
                skus_processed=skus_processed,
                error_message=None,
            )

            logger.info(
                "Inventory reconciliation completed: %s SKUs",
                skus_processed,
            )
            return

        except OperationalError as exc:
            if not _is_sqlite_lock_error(exc):
                await _write_audit(
                    status="FAILED",
                    skus_processed=0,
                    error_message=str(exc)[:1000],
                )
                logger.exception("Reconciliation database error")
                return

            last_error = str(exc)

            logger.warning(
                "SQLite locking error on attempt %s/%s",
                attempt,
                MAX_RETRIES,
            )

            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.2 * attempt + random.uniform(0, 0.1))

        except Exception as exc:
            await _write_audit(
                status="FAILED",
                skus_processed=0,
                error_message=str(exc)[:1000],
            )
            logger.exception("Reconciliation failed")
            return

    await _write_audit(
        status="RETRY_FALLBACK",
        skus_processed=0,
        error_message=f"Retries exhausted: {last_error}"[:1000],
    )

    logger.error("Reconciliation stopped after retry attempts")


def _is_sqlite_lock_error(exc: OperationalError) -> bool:
    """Identify SQLite database locking errors."""

    original_error = exc.orig

    return (
        isinstance(original_error, sqlite3.OperationalError)
        and (
            "locked" in str(original_error).lower()
            or "busy" in str(original_error).lower()
        )
    )


async def _write_audit(
    status: str,
    skus_processed: int,
    error_message: str | None,
) -> None:
    """Write an audit record in its own transaction."""

    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(
                ReconciliationAuditLog(
                    timestamp=datetime.utcnow(),
                    status=status,
                    skus_processed=skus_processed,
                    error_message=error_message,
                )
            )
