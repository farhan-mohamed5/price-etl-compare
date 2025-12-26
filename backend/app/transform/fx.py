from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import FXRate

def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)

def fx_to_aed(db: Session, amount: float, currency: str, as_of: datetime, target: str = "AED") -> float:
    c = currency.upper()
    if c == target.upper():
        return float(amount)

    fx_date = _midnight(as_of.date())

    # Try direct: c -> AED
    stmt = select(FXRate).where(
        FXRate.fx_date == fx_date,
        FXRate.base_currency == c,
        FXRate.quote_currency == target.upper(),
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row:
        return float(amount) * float(row.rate)

    # Try inverse: AED -> c
    stmt2 = select(FXRate).where(
        FXRate.fx_date == fx_date,
        FXRate.base_currency == target.upper(),
        FXRate.quote_currency == c,
    )
    row2 = db.execute(stmt2).scalar_one_or_none()
    if row2 and float(row2.rate) != 0:
        return float(amount) / float(row2.rate)

    raise ValueError(f"No FX rate for {c}↔{target} on {fx_date.date().isoformat()}")
