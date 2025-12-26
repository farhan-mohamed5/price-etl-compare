from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Numeric, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from .db import Base

class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. V-A
    name: Mapped[str] = mapped_column(String, nullable=False)
    default_currency: Mapped[str] = mapped_column(String, nullable=False)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. P-RTX4070
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

class ProductAlias(Base):
    __tablename__ = "product_aliases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    vendor_sku: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    vendor_name_raw: Mapped[str] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("vendor_id", "vendor_sku", name="uq_alias_vendor_sku"),
        Index("ix_alias_vendor_sku", "vendor_id", "vendor_sku"),
    )

class FXRate(Base):
    __tablename__ = "fx_rates"
    # rate converts 1 unit of base_currency into quote_currency
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fx_date: Mapped[date] = mapped_column(DateTime(timezone=False), nullable=False)  # stored at midnight
    base_currency: Mapped[str] = mapped_column(String, nullable=False)
    quote_currency: Mapped[str] = mapped_column(String, nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)

    __table_args__ = (
        UniqueConstraint("fx_date", "base_currency", "quote_currency", name="uq_fx"),
        Index("ix_fx_lookup", "fx_date", "base_currency", "quote_currency"),
    )

class RawIngestion(Base):
    __tablename__ = "raw_ingestions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    stored_path: Mapped[str] = mapped_column(String, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False)  # PENDING, PROCESSED, FAILED
    message: Mapped[str] = mapped_column(String, nullable=True)

class Price(Base):
    __tablename__ = "prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price_aed: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    source_ingestion_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_ingestions.id"), nullable=False)

    __table_args__ = (
        Index("ix_prices_product_time", "product_id", "observed_at"),
        Index("ix_prices_vendor_time", "vendor_id", "observed_at"),
    )

class Rejection(Base):
    __tablename__ = "rejections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_ingestions.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    raw_row: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

class Run(Base):
    __tablename__ = "etl_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)
    status: Mapped[str] = mapped_column(String, default="RUNNING", nullable=False)  # RUNNING, DONE, PARTIAL
    processed_ingestions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loaded_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
