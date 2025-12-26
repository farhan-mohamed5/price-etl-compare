import json
from datetime import datetime
from .types import CanonicalPriceRow

def parse_vendor_b(path: str, vendor_id: str):
    # JSON: { "asOf": "...", "items":[{"partNumber":"...","title":"...","pricing":{"amount":..., "ccy":"USD"}}]}
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    as_of = datetime.fromisoformat(payload["asOf"])
    items = payload.get("items", [])
    for idx, item in enumerate(items, start=1):
        pricing = item.get("pricing") or {}
        yield idx, CanonicalPriceRow(
            vendor_id=vendor_id,
            vendor_sku=str(item.get("partNumber") or "").strip(),
            vendor_name_raw=str(item.get("title") or "").strip() or None,
            price=float(pricing.get("amount") or 0),
            currency=str(pricing.get("ccy") or "").strip().upper(),
            observed_at=as_of,
        )
