from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from .models import RawIngestion, Price, Rejection, Run
from .transform.vendor_a import parse_vendor_a
from .transform.vendor_b import parse_vendor_b
from .transform.vendor_c import parse_vendor_c
from .transform.normalize import resolve_product_id
from .transform.fx import fx_to_aed

PARSERS = {
    "vendor_a": parse_vendor_a,
    "vendor_b": parse_vendor_b,
    "vendor_c": parse_vendor_c,
}

VENDOR_ID_MAP = {
    "vendor_a": "V-A",
    "vendor_b": "V-B",
    "vendor_c": "V-C",
}

def run_etl(db: Session) -> dict:
    run = Run()
    db.add(run)
    db.commit()
    db.refresh(run)

    pending = db.execute(select(RawIngestion).where(RawIngestion.status == "PENDING").order_by(RawIngestion.id)).scalars().all()

    loaded = 0
    rejected = 0
    processed_ing = 0

    for ing in pending:
        processed_ing += 1
        vendor_id = ing.vendor_id
        # pick parser based on vendor_id
        if vendor_id == "V-A":
            parser = PARSERS["vendor_a"]
        elif vendor_id == "V-B":
            parser = PARSERS["vendor_b"]
        elif vendor_id == "V-C":
            parser = PARSERS["vendor_c"]
        else:
            ing.status = "FAILED"
            ing.message = f"Unknown vendor_id: {vendor_id}"
            db.commit()
            continue

        try:
            for rownum, crow in parser(ing.stored_path, vendor_id):
                # basic validations
                if not crow.vendor_sku:
                    rejected += 1
                    db.add(Rejection(ingestion_id=ing.id, row_number=rownum, reason="missing_vendor_sku", raw_row=crow.model_dump()))
                    continue
                if crow.price <= 0:
                    rejected += 1
                    db.add(Rejection(ingestion_id=ing.id, row_number=rownum, reason="non_positive_price", raw_row=crow.model_dump()))
                    continue
                if not crow.currency:
                    rejected += 1
                    db.add(Rejection(ingestion_id=ing.id, row_number=rownum, reason="missing_currency", raw_row=crow.model_dump()))
                    continue

                product_id = resolve_product_id(db, vendor_id, crow.vendor_sku)
                if not product_id:
                    rejected += 1
                    db.add(Rejection(ingestion_id=ing.id, row_number=rownum, reason="unknown_product_alias", raw_row=crow.model_dump()))
                    continue

                try:
                    price_aed = fx_to_aed(db, crow.price, crow.currency, crow.observed_at, target="AED")
                except Exception as e:
                    rejected += 1
                    db.add(Rejection(ingestion_id=ing.id, row_number=rownum, reason=f"fx_error:{str(e)}", raw_row=crow.model_dump()))
                    continue

                db.add(Price(
                    product_id=product_id,
                    vendor_id=vendor_id,
                    observed_at=crow.observed_at,
                    currency=crow.currency,
                    price=crow.price,
                    price_aed=price_aed,
                    source_ingestion_id=ing.id,
                ))
                loaded += 1

            ing.status = "PROCESSED"
            ing.message = "ok"
            db.commit()
        except Exception as e:
            ing.status = "FAILED"
            ing.message = str(e)
            db.commit()

    run.finished_at = datetime.utcnow()
    run.status = "DONE"
    run.processed_ingestions = processed_ing
    run.loaded_rows = loaded
    run.rejected_rows = rejected
    db.commit()

    return {
        "run_id": run.id,
        "processed_ingestions": processed_ing,
        "loaded_rows": loaded,
        "rejected_rows": rejected,
    }
