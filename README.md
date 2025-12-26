# price-etl-compare

Multi-source **computer parts** price ETL:
- ingest vendor feeds (CSV/JSON)
- normalize products (via alias mapping)
- convert currencies to AED using stored FX rates
- store price history
- compare vendors (cheapest / spread / history)

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

## Demo script (2 minutes)
1. Seed (`POST /admin/seed`)
2. Ingest 3 feeds
3. Run ETL
4. Open:
   - `GET /cheapest` (who’s cheapest per product)
   - `GET /compare/{product_id}` (spread and all vendors)
   - `GET /history/{product_id}` (time-series)

Then ingest `samples/vendor_a_bad.csv` and re-run ETL to show rejections:
```bash
curl -F "file=@samples/vendor_a_bad.csv" http://127.0.0.1:8000/ingest/vendor_a
curl -X POST http://127.0.0.1:8000/run-etl
curl http://127.0.0.1:8000/rejections
```
