
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine, Base
from app.models import Product


async def seed_inventory():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(Product.sku == "SKU-001")
        )
        product = result.scalar_one_or_none()

        if product is None:
            session.add(
                Product(
                    sku="SKU-001",
                    name="Wireless Mouse",
                    stock_quantity=10,
                    warehouse_location="PUNE-WH-01",
                    base_price_usd=19.99,
                    is_active=True,
                )
            )
            await session.commit()
            print("Sample product SKU-001 created.")
        else:
            print("Sample product SKU-001 already exists.")


if __name__ == "__main__":
    asyncio.run(seed_inventory())
