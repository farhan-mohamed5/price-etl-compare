from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Vendor, Product, ProductAlias, FXRate

def seed(db: Session):
    # Vendors
    vendors = [
        Vendor(id="V-A", name="GulfTech Parts", default_currency="AED"),
        Vendor(id="V-B", name="US Parts Direct", default_currency="USD"),
        Vendor(id="V-C", name="EuroComp Store", default_currency="EUR"),
    ]
    for v in vendors:
        if not db.execute(select(Vendor).where(Vendor.id == v.id)).scalar_one_or_none():
            db.add(v)
    # IMPORTANT: flush vendors so FK checks for aliases won’t fail
    db.flush()

    # Products
    products = [
        Product(id="P-RTX4070", canonical_name="NVIDIA GeForce RTX 4070 12GB", category="GPU"),
        Product(id="P-RYZEN7800X3D", canonical_name="AMD Ryzen 7 7800X3D", category="CPU"),
        Product(id="P-B650", canonical_name="MSI B650 ATX Motherboard", category="Motherboard"),
        Product(id="P-32GBDDR5", canonical_name="32GB (2x16GB) DDR5-6000 RAM Kit", category="Memory"),
        Product(id="P-1TB_NVME", canonical_name="1TB NVMe Gen4 SSD", category="Storage"),
        Product(id="P-PSU750", canonical_name="750W 80+ Gold PSU", category="PSU"),
    ]
    for p in products:
        if not db.execute(select(Product).where(Product.id == p.id)).scalar_one_or_none():
            db.add(p)
    # IMPORTANT: flush products so aliases can safely reference them
    db.flush()

    # Vendor SKU -> product mapping (aliases)
    aliases = [
        # Vendor A (AED, CSV)
        ("V-A", "GT-RTX4070-12G", "P-RTX4070", "RTX 4070 12GB (GulfTech)"),
        ("V-A", "GT-R7-7800X3D", "P-RYZEN7800X3D", "Ryzen 7 7800X3D"),
        ("V-A", "GT-MSI-B650-ATX", "P-B650", "MSI B650 ATX"),
        ("V-A", "GT-DDR5-32-6000", "P-32GBDDR5", "DDR5 32GB 6000"),
        ("V-A", "GT-NVME-1TB-G4", "P-1TB_NVME", "NVMe 1TB Gen4"),
        ("V-A", "GT-PSU-750-GOLD", "P-PSU750", "PSU 750W Gold"),
        # Vendor B (USD, JSON)
        ("V-B", "PN-4070-12G", "P-RTX4070", "NVIDIA RTX 4070 12GB"),
        ("V-B", "PN-7800X3D", "P-RYZEN7800X3D", "AMD Ryzen 7 7800X3D"),
        ("V-B", "PN-MB-B650", "P-B650", "MSI B650 ATX Motherboard"),
        ("V-B", "PN-RAM-32-D5-6000", "P-32GBDDR5", "32GB DDR5 6000 Kit"),
        ("V-B", "PN-SSD-1TB-NVME4", "P-1TB_NVME", "1TB NVMe Gen4 SSD"),
        ("V-B", "PN-PSU-750-G", "P-PSU750", "750W 80+ Gold PSU"),
        # Vendor C (EUR, CSV)
        ("V-C", "EC-RTX4070", "P-RTX4070", "GeForce RTX 4070 12GB"),
        ("V-C", "EC-R7-7800X3D", "P-RYZEN7800X3D", "Ryzen 7 7800X3D"),
        ("V-C", "EC-B650-MSI", "P-B650", "MSI B650 ATX"),
        ("V-C", "EC-DDR5-32-6000", "P-32GBDDR5", "DDR5 32GB 6000"),
        ("V-C", "EC-NVME-1TB-G4", "P-1TB_NVME", "NVMe 1TB Gen4"),
        ("V-C", "EC-PSU-750-GOLD", "P-PSU750", "PSU 750W Gold"),
    ]
    for vendor_id, vendor_sku, product_id, vendor_name_raw in aliases:
        exists = db.execute(select(ProductAlias).where(
            ProductAlias.vendor_id == vendor_id,
            ProductAlias.vendor_sku == vendor_sku,
        )).scalar_one_or_none()
        if not exists:
            db.add(ProductAlias(
                vendor_id=vendor_id,
                vendor_sku=vendor_sku,
                product_id=product_id,
                vendor_name_raw=vendor_name_raw,
            ))

    # FX rates (as-of 2025-12-20) - deterministic for demo
    fx_date = datetime(2025, 12, 20)
    fx_rows = [
        ("USD", "AED", 3.6725),
        ("EUR", "AED", 4.0200),
        ("AED", "USD", 0.2723),
        ("AED", "EUR", 0.2488),
    ]
    for base, quote, rate in fx_rows:
        exists = db.execute(select(FXRate).where(
            FXRate.fx_date == fx_date,
            FXRate.base_currency == base,
            FXRate.quote_currency == quote,
        )).scalar_one_or_none()
        if not exists:
            db.add(FXRate(
                fx_date=fx_date,
                base_currency=base,
                quote_currency=quote,
                rate=rate,
            ))

    db.commit()
