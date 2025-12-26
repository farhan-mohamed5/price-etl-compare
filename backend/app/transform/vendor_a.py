import csv
from datetime import datetime
from .types import CanonicalPriceRow

def parse_vendor_a(path: str, vendor_id: str):
    # CSV: sku,name,price,currency,date
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # 1 is header
            yield i, CanonicalPriceRow(
                vendor_id=vendor_id,
                vendor_sku=(row.get("sku") or "").strip(),
                vendor_name_raw=(row.get("name") or "").strip() or None,
                price=float(row.get("price") or 0),
                currency=(row.get("currency") or "").strip().upper(),
                observed_at=datetime.fromisoformat((row.get("date") or "").strip()),
            )
