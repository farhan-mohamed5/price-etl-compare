from pydantic import BaseModel
from datetime import datetime

class CanonicalPriceRow(BaseModel):
    vendor_id: str
    vendor_sku: str
    vendor_name_raw: str | None = None
    observed_at: datetime
    currency: str
    price: float
