from app.core.db import Base, get_engine
from app import models  # IMPORTANT: ensures all models are registered

engine = get_engine()
if engine is None:
    raise RuntimeError("Missing DATABASE_URL")

Base.metadata.create_all(bind=engine)
print("Tables created/updated.")