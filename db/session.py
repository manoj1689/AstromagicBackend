from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import SQLALCHEMY_DATABASE_URL
from db.base import Base



# Create database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session factory
# SessionLocal setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SessionLocal = sessionmaker(bind=engine)
# Base.metadata.drop_all(engine, tables=[User.__table__])
# Base.metadata.create_all(engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()