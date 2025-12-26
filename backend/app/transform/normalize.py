from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import ProductAlias

def resolve_product_id(db: Session, vendor_id: str, vendor_sku: str) -> str | None:
    if not vendor_sku:
        return None
    stmt = select(ProductAlias).where(
        ProductAlias.vendor_id == vendor_id,
        ProductAlias.vendor_sku == vendor_sku,
    )
    alias = db.execute(stmt).scalar_one_or_none()
    return alias.product_id if alias else None
