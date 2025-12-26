# price-etl-compare

Multi-source **computer parts** price ETL + comparison API. Ingests vendor feeds (CSV/JSON), maps messy vendor SKUs to canonical products via alias tables, converts all prices to **AED** using stored **FX rates**, and writes a clean **price history** you can query for cheapest vendor, spreads, and time-series trends.

---

## What this project demonstrates

- Realistic **ETL pipeline** patterns (ingest → validate → normalize → transform → persist)
- Handling messy vendor data using **alias mapping** (vendor SKU → canonical product)
- **Currency normalization** with reproducible FX rates (seeded once)
- A small but complete **query API** for comparisons and history
- **Rejections** for bad inputs (so the pipeline stays trustworthy)

---

## Tech stack

- **Python 3.11+**
- **FastAPI** + **Uvicorn** (HTTP API)
- **SQLAlchemy** + **PostgreSQL** (storage)
- **psycopg** (Postgres driver)
- **Docker Compose** (local Postgres)
- Vendor feed formats:
  - CSV (e.g., Vendor A / Vendor C)
  - JSON (e.g., Vendor B)

---

## Core concepts / data model

- **vendors**: where the feed comes from + default currency
- **products**: canonical product definitions (IDs like `P-RTX4070`)
- **product_aliases**: vendor SKU/name → canonical product ID
- **fx_rates**: base/quote currency rates stored for a specific date (demo is deterministic)
- (your ETL tables): ingestions / price history / rejections (depending on your schema)

---

## API overview (common routes)

- `POST /admin/seed`  
  Seeds vendors, products, SKU aliases, and FX rates (one-time per fresh DB).

- `POST /ingest/vendor_a` (CSV upload)  
- `POST /ingest/vendor_b` (JSON upload)  
- `POST /ingest/vendor_c` (CSV upload)  
  Stores raw uploads as “pending ingestion”.

- `POST /run-etl`  
  Processes pending ingestions → writes normalized prices → logs any rejections.

- `GET /products`  
  Lists canonical products.

- `GET /cheapest`  
  Cheapest vendor per product (in AED).

- `GET /compare/{product_id}`  
  All vendor prices for one product + spread.

- `GET /history/{product_id}`  
  Time-series price history for one product.

- `GET /rejections`  
  Shows rows rejected during ingest/ETL (e.g., missing required fields, invalid currency).

---

## Quick start

### 1) Start Postgres
```bash
cd infra
docker compose up -d
```

### 2) Run the API
```bash
cd ../backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/price_etl"
uvicorn app.main:app --reload --port 8000
```

### 3) Seed FX + product mapping (one time)
```bash
curl -X POST http://127.0.0.1:8000/admin/seed
```

### 4) Ingest sample vendor feeds
```bash
# from repo root
curl -F "file=@samples/vendor_a.csv" http://127.0.0.1:8000/ingest/vendor_a
curl -F "file=@samples/vendor_b.json" http://127.0.0.1:8000/ingest/vendor_b
curl -F "file=@samples/vendor_c.csv" http://127.0.0.1:8000/ingest/vendor_c
```

### 5) Run ETL on all pending ingestions
```bash
curl -X POST http://127.0.0.1:8000/run-etl
```

### 6) Compare vendors
```bash
curl http://127.0.0.1:8000/products
curl http://127.0.0.1:8000/cheapest
curl http://127.0.0.1:8000/compare/P-RTX4070
curl http://127.0.0.1:8000/history/P-RTX4070
```

---

## Demo script (2 minutes)

1. Seed (`POST /admin/seed`)
2. Ingest 3 feeds
3. Run ETL
4. Open:
   - `GET /cheapest` (who’s cheapest per product)
   - `GET /compare/{product_id}` (spread and all vendors)
   - `GET /history/{product_id}` (time-series)

Then ingest a broken file to show validation + rejections:
```bash
curl -F "file=@samples/vendor_a_bad.csv" http://127.0.0.1:8000/ingest/vendor_a
curl -X POST http://127.0.0.1:8000/run-etl
curl http://127.0.0.1:8000/rejections
```

---

## Notes

- If `POST /admin/seed` fails with FK errors, it usually means the seed inserts aliases before vendors/products are flushed/committed. Fix: flush vendors/products before alias inserts.
- This project is designed to be easy to demo with `curl` and a fresh Postgres container.

