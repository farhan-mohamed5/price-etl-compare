import csv
from datetime import datetime
from .types import CanonicalPriceRow

def parse_vendor_c(path: str, vendor_id: str):
    # CSV: vendor_code,desc,unit_price,ccy,as_of
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            yield i, CanonicalPriceRow(
                vendor_id=vendor_id,
                vendor_sku=(row.get("vendor_code") or "").strip(),
                vendor_name_raw=(row.get("desc") or "").strip() or None,
                price=float(row.get("unit_price") or 0),
                currency=(row.get("ccy") or "").strip().upper(),
                observed_at=datetime.fromisoformat((row.get("as_of") or "").strip()),
            )
