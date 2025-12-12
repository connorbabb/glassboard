from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- RDS Postgres configuration ---
RDS_HOST = "glassboard-rds.c1ymcqk8mlq7.us-west-2.rds.amazonaws.com"
RDS_DB = "glassboard-rds"
RDS_USER = "adminuser"
RDS_PASSWORD = "BlueSpartan03!"
RDS_PORT = 5432

DATABASE_URL = f"postgresql+psycopg2://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/glassboard"

engine = create_engine(
    DATABASE_URL, 
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
