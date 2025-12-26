from pydantic import BaseModel
import os

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/price_etl")
    aed_currency: str = "AED"
    storage_dir: str = os.getenv("STORAGE_DIR", "./storage")

settings = Settings()
