from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from .db import engine, Base, get_db
from .models import Vendor, Product, RawIngestion, Price, Rejection
from .storage import save_upload_bytes
from .etl import run_etl
from .seed import seed

app = FastAPI(title="Price ETL Compare", version="0.1.0")

@app.on_event("startup")
def on_startup():
    # MVP: create tables automatically
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.post("/admin/seed")
def admin_seed(db: Session = Depends(get_db)):
    seed(db)
    return {"seeded": True}

@app.post("/ingest/{vendor_key}")
async def ingest(vendor_key: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    vendor_key = vendor_key.lower().strip()
    vendor_map = {"vendor_a":"V-A", "vendor_b":"V-B", "vendor_c":"V-C"}
    if vendor_key not in vendor_map:
        raise HTTPException(status_code=400, detail="Unknown vendor. Use vendor_a, vendor_b, vendor_c")
    vendor_id = vendor_map[vendor_key]

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    stored_path = save_upload_bytes(file.filename or f"{vendor_key}.dat", data)

    ing = RawIngestion(
        vendor_id=vendor_id,
        file_name=file.filename or "upload",
        stored_path=stored_path,
        status="PENDING",
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)

    return {"ingestion_id": ing.id, "vendor_id": vendor_id, "stored_path": stored_path, "status": ing.status}

@app.post("/run-etl")
def run_all_etl(db: Session = Depends(get_db)):
    return run_etl(db)

@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.execute(select(Product).order_by(Product.category, Product.id)).scalars().all()
    return [{"product_id": p.id, "name": p.canonical_name, "category": p.category} for p in products]

@app.get("/cheapest")
def cheapest(db: Session = Depends(get_db)):
    # latest observed_at per (product,vendor)
    sub = (
        select(
            Price.product_id,
            Price.vendor_id,
            func.max(Price.observed_at).label("max_ts")
        )
        .group_by(Price.product_id, Price.vendor_id)
        .subquery()
    )
    latest = (
        select(Price.product_id, Price.vendor_id, Price.price_aed, Price.observed_at)
        .join(sub, (Price.product_id==sub.c.product_id) & (Price.vendor_id==sub.c.vendor_id) & (Price.observed_at==sub.c.max_ts))
        .subquery()
    )

    # now choose min price per product
    rows = db.execute(
        select(
            latest.c.product_id,
            func.min(latest.c.price_aed).label("min_aed")
        ).group_by(latest.c.product_id)
    ).all()

    out = []
    for product_id, min_aed in rows:
        # find which vendor(s) match
        vendors = db.execute(
            select(latest.c.vendor_id, latest.c.price_aed, latest.c.observed_at)
            .where(latest.c.product_id == product_id, latest.c.price_aed == min_aed)
        ).all()
        p = db.execute(select(Product).where(Product.id == product_id)).scalar_one()
        out.append({
            "product_id": product_id,
            "product": p.canonical_name,
            "cheapest_aed": float(min_aed),
            "vendors": [{"vendor_id": v[0], "price_aed": float(v[1]), "as_of": v[2].isoformat()} for v in vendors]
        })
    return out

@app.get("/compare/{product_id}")
def compare(product_id: str, db: Session = Depends(get_db)):
    # latest price per vendor for this product
    sub = (
        select(
            Price.vendor_id,
            func.max(Price.observed_at).label("max_ts")
        )
        .where(Price.product_id == product_id)
        .group_by(Price.vendor_id)
        .subquery()
    )
    latest = db.execute(
        select(Price.vendor_id, Price.price_aed, Price.observed_at)
        .join(sub, (Price.vendor_id==sub.c.vendor_id) & (Price.observed_at==sub.c.max_ts))
        .where(Price.product_id == product_id)
        .order_by(Price.price_aed.asc())
    ).all()

    p = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Unknown product_id")

    if not latest:
        return {"product_id": product_id, "product": p.canonical_name, "vendors": [], "spread_aed": None, "spread_pct": None}

    prices = [float(x[1]) for x in latest]
    spread = max(prices) - min(prices)
    spread_pct = (spread / min(prices)) * 100 if min(prices) > 0 else None

    return {
        "product_id": product_id,
        "product": p.canonical_name,
        "vendors": [{"vendor_id": v[0], "price_aed": float(v[1]), "as_of": v[2].isoformat()} for v in latest],
        "spread_aed": float(spread),
        "spread_pct": float(spread_pct) if spread_pct is not None else None
    }

@app.get("/history/{product_id}")
def history(product_id: str, db: Session = Depends(get_db)):
    p = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Unknown product_id")
    rows = db.execute(
        select(Price.vendor_id, Price.observed_at, Price.price_aed)
        .where(Price.product_id == product_id)
        .order_by(Price.observed_at.asc())
    ).all()
    return {
        "product_id": product_id,
        "product": p.canonical_name,
        "points": [{"vendor_id": r[0], "t": r[1].isoformat(), "price_aed": float(r[2])} for r in rows]
    }

@app.get("/ingestions")
def ingestions(db: Session = Depends(get_db)):
    rows = db.execute(select(RawIngestion).order_by(RawIngestion.id.desc()).limit(50)).scalars().all()
    return [{
        "id": r.id,
        "vendor_id": r.vendor_id,
        "file_name": r.file_name,
        "status": r.status,
        "message": r.message,
        "ingested_at": r.ingested_at.isoformat(),
    } for r in rows]

@app.get("/rejections")
def rejections(db: Session = Depends(get_db)):
    rows = db.execute(select(Rejection).order_by(Rejection.id.desc()).limit(100)).scalars().all()
    return [{
        "id": r.id,
        "ingestion_id": r.ingestion_id,
        "row_number": r.row_number,
        "reason": r.reason,
        "raw_row": r.raw_row,
        "created_at": r.created_at.isoformat(),
    } for r in rows]
